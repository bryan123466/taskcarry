# Building a release

Build from a clean, reviewed commit with Python 3.11+, Git and the standard Python wheel build tools available. The product archive contains only the positive allowlist in `scripts/build_trial.py`; private state and local validation work are excluded.

```text
python scripts/build_trial.py --check
python scripts/build_trial.py --profile product --source-commit <full-commit-SHA> --out <new-output-directory-outside-checkout>
```

The second command verifies that the selected source matches that commit, builds the wheel, checks its packaged Skills, and creates the portable product ZIP and release manifest. The outer `TaskCarry/` folder contains the first-use prompt and versioned `toolkit/`.

For the Windows x64 bundle, download the two exact upstream archives named in `scripts/build_windows.py` into a separate runtime input directory. That script checks their SHA-256 hashes and retains the upstream licenses and source links. It does not download or install system tools.

```text
python scripts/build_windows.py --product-dir <product-output-directory> --runtime-dir <runtime-input-directory>
```

The Windows artifact adds embedded Python, MinGit, CLI/MCP launchers, `WINDOWS.md`, and a per-file `WINDOWS_MANIFEST.json`. Its release manifest retains the original TaskCarry source commit and wheel. The third-party runtime licenses remain separate from TaskCarry's MIT license.

Before publication, run the source tests, installed-wheel checks, and final-package installation/update checks in disposable projects outside a parent Git repository. Verify the exact source commit in CI, then attach the actual results and checksums to the release. Never treat a configured test or historical result as a new run.

## 简体中文

发行从已复核的确定提交构建。先执行上面的源码检查和产品包构建，再按需要加入 Windows 运行环境；输出目录须位于源码目录之外。构建器按白名单选择文件，核对源码提交、wheel、随包 Skills 与上游运行环境的哈希，并保留第三方许可。发布前在隔离项目中检查最终包的新装、更新和实际工具调用，将本次结果附在发行页。

## 繁體中文

發行從已複核的確定提交建置。先執行上方的原始碼檢查與產品包建置，再依需要加入 Windows 執行環境；輸出目錄須位於原始碼目錄之外。建置器依白名單選取檔案，核對原始碼提交、wheel、隨附 Skills 與上游執行環境雜湊，保留第三方授權。發布前在隔離專案檢查最終套件的新裝、更新與實際工具呼叫，將本次結果附在發行頁。
