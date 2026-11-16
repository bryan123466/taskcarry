import { spawn } from "node:child_process";
import { mkdtemp, readFile, realpath, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { setTimeout as delay } from "node:timers/promises";

export async function waitFor(check, description, timeoutMs = 12_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const value = await check();
    if (value) return value;
    await delay(50);
  }
  throw new Error("等待超时 " + description);
}

export async function openChrome(runDirectory) {
  const root = await realpath(runDirectory);
  const profile = await mkdtemp(path.join(root, "chrome-"));
  const chrome = process.env.RC8_CHROME_PATH || process.env.RC8_TEST_CHROME || (process.platform === "win32"
    ? path.join(process.env.ProgramFiles || process.env["ProgramFiles(x86)"] || "", "Google", "Chrome", "Application", "chrome.exe")
    : process.platform === "darwin" ? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" : "google-chrome");
  const child = spawn(chrome, [
    "--headless=new", "--window-size=1400,1050", "--no-first-run", "--no-default-browser-check",
    "--disable-background-networking", "--disable-component-update", "--disable-extensions",
    "--disable-sync", "--disable-background-timer-throttling", "--disable-breakpad",
    "--no-proxy-server", "--host-resolver-rules=MAP * ~NOTFOUND",
    "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0",
    "--user-data-dir=" + profile, "about:blank"
  ], {
    env: { ...process.env, TEMP: profile, TMP: profile },
    stdio: ["ignore", "ignore", "pipe"], windowsHide: true
  });
  let processError;
  let stderr = "";
  let exited = false;
  child.once("error", error => { processError = error; exited = true; });
  child.once("exit", () => { exited = true; });
  child.stderr.on("data", data => { stderr = (stderr + data).slice(-4000); });

  let socket;
  let nextId = 0;
  const pending = new Map();
  const activity = { requests: [], failures: [], external: [], exceptions: [] };
  const requestURLs = new Map();

  function send(method, params = {}) {
    return new Promise((resolve, reject) => {
      if (socket?.readyState !== WebSocket.OPEN) return reject(new Error("Chrome DevTools 已断开"));
      const id = ++nextId;
      const timeout = setTimeout(() => {
        pending.delete(id);
        reject(new Error("Chrome DevTools 调用超时 " + method));
      }, 8_000);
      pending.set(id, { resolve, reject, timeout });
      socket.send(JSON.stringify({ id, method, params }));
    });
  }

  function onMessage(event) {
    const { id, method, params, result, error } = JSON.parse(event.data);
    if (id) {
      const request = pending.get(id);
      if (!request) return;
      pending.delete(id);
      clearTimeout(request.timeout);
      if (error) request.reject(new Error(error.message));
      else request.resolve(result);
      return;
    }
    switch (method) {
      case "Network.requestWillBeSent":
        requestURLs.set(params.requestId, params.request.url);
        activity.requests.push({ url: params.request.url, method: params.request.method, type: params.type });
        break;
      case "Network.loadingFailed":
        activity.failures.push({ url: requestURLs.get(params.requestId), error: params.errorText });
        break;
      case "Network.webSocketCreated":
        activity.external.push(params.url);
        break;
      case "Fetch.requestPaused":
        activity.external.push(params.request.url);
        send("Fetch.failRequest", { requestId: params.requestId, errorReason: "BlockedByClient" })
          .catch(error => activity.exceptions.push(error.message));
        break;
      case "Runtime.exceptionThrown":
        activity.exceptions.push(params.exceptionDetails);
        break;
      case "Runtime.consoleAPICalled":
        if (params.type === "error") {
          activity.exceptions.push(params.args.map(arg => arg.description ?? arg.value));
        }
        break;
    }
  }

  async function close() {
    try {
      if (socket?.readyState === WebSocket.OPEN) {
        await Promise.race([send("Browser.close").catch(() => {}), delay(800)]);
        socket.close();
      }
      if (!exited && child.pid) child.kill();
      if (!exited) await waitFor(() => exited, "Chrome 退出", 3000);
    } finally {
      const scratch = await realpath(profile);
      if (path.dirname(scratch) === root && path.basename(scratch).startsWith("chrome-")) {
        await rm(scratch, { recursive: true, force: true, maxRetries: 6, retryDelay: 100 });
      }
    }
  }

  try {
    const port = await waitFor(async () => {
      if (processError) throw processError;
      if (exited) throw new Error("Chrome 提前退出 " + stderr);
      try {
        const text = await readFile(path.join(profile, "DevToolsActivePort"), "utf8");
        const value = Number(text.split(/\r?\n/)[0]);
        return Number.isInteger(value) && value > 0 && value < 65536 ? value : null;
      } catch (error) {
        if (error.code !== "ENOENT") throw error;
        return null;
      }
    }, "Chrome 本地调试端口");
    const targets = await (await fetch("http://127.0.0.1:" + port + "/json/list", {
      signal: AbortSignal.timeout(5000)
    })).json();
    const page = targets.find(target => target.type === "page");
    if (!page) throw new Error("Chrome 没有可用的测试页面");
    socket = new WebSocket(page.webSocketDebuggerUrl);
    socket.addEventListener("message", onMessage);
    socket.addEventListener("close", () => {
      for (const request of pending.values()) {
        clearTimeout(request.timeout);
        request.reject(new Error("Chrome DevTools 已关闭"));
      }
      pending.clear();
    });
    await waitFor(() => {
      if (socket.readyState === WebSocket.CLOSED) throw new Error("Chrome DevTools 连接失败");
      return socket.readyState === WebSocket.OPEN;
    }, "Chrome DevTools WebSocket");
    await send("Page.enable");
    await send("Runtime.enable");
    await send("Network.enable");
    await send("Fetch.enable", { patterns: [{ urlPattern: "http://*" }, { urlPattern: "https://*" }] });
    const version = await send("Browser.getVersion");

    return {
      activity, version, close, send,
      async evaluate(fn, ...args) {
        const expression = "(" + fn.toString() + ")(" + args.map(arg => JSON.stringify(arg)).join(",") + ")";
        const reply = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
        if (reply.exceptionDetails) {
          throw new Error(reply.exceptionDetails.exception?.description ?? reply.exceptionDetails.text);
        }
        return reply.result.value;
      },
      async screenshot(file) {
        const { data } = await send("Page.captureScreenshot", { format: "png" });
        await writeFile(file, Buffer.from(data, "base64"));
      }
    };
  } catch (error) {
    await close().catch(() => {});
    throw error;
  }
}
