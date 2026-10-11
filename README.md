# libfprint-egis0575 — EgisTec EH575 (1c7a:0575) Linux 指纹驱动

> [English version](README.en.md)

让 EgisTec EH575 指纹传感器（Acer SFX14-41G、Swift SF314-42 等机型）在 Linux 上真正可用
（识别精度达到 KDE 解锁水准）。驱动源码随本仓库分发（`libfprint/` 子树，
含上游 libfprint 完整历史），逆向研究与工程决策全部留档 docs/，最终目标
是产出可提交给 [libfprint 上游](https://gitlab.freedesktop.org/libfprint/libfprint)的驱动。

## 安装

- **Arch**：`yay -S libfprint-egis0575`（AUR 包跟随上游
  [cosct/libfprint-egis0575](https://github.com/cosct/libfprint-egis0575)，
  **不含**本 fork 的修复）
- **Debian / Fedora**：[本 fork 的 Releases](https://github.com/edi194/libfprint-egis0575/releases)
  提供 `.deb` 与 `.rpm`（每个 `egis0575-v*` 标签经 release workflow 自动构建发布）：
  `sudo dnf install ./libfprint-egis0575-<版本>.<dist>.x86_64.rpm`
  ——该包会替换发行版 libfprint；回滚：`sudo dnf install --allowerasing libfprint`
- **本地构建（Fedora）**：

      sudo dnf install -y meson ninja-build gcc gcc-c++ rpm-build \
        glib2-devel libgusb-devel pixman-devel libusb1-devel \
        systemd-devel openssl-devel libgudev-devel
      git clone https://github.com/edi194/libfprint-egis0575.git
      cd libfprint-egis0575
      mkdir -p ~/rpmbuild/{SOURCES,SPECS}
      git archive --prefix=libfprint-egis0575-egis0575-v0.2.3/ HEAD \
        | gzip -9 > ~/rpmbuild/SOURCES/libfprint-egis0575-0.2.3.tar.gz
      cp packaging/rpm/libfprint-egis0575.spec ~/rpmbuild/SPECS/
      rpmbuild -ba ~/rpmbuild/SPECS/libfprint-egis0575.spec
      sudo dnf install ~/rpmbuild/RPMS/x86_64/libfprint-egis0575-0.2.3-1.*.x86_64.rpm

- **本地开发（Arch）**：`makepkg -f -i`（根目录 PKGBUILD，从工作树构建）
- **⚠ 升级注意**：v0.2.0 的模板序列化丢失取向字段，该版本录入的指纹
  无法通过新驱动验证——升级后请 `fprintd-delete` 删除旧指纹并重新录入

## Fork 状态（2026-10-11）

本 fork（[edi194/libfprint-egis0575](https://github.com/edi194/libfprint-egis0575)）
基于上游 master（`53221b9`），追加两项经真机验证的可靠性修复：

- **F1 —— 每次 claim 都执行完整校准链**（`SM_CAL_START` 门）：仅重新上传的
  re-arm（`POST_RESET` → `73 14 ec`）在 Linux 式会话收尾后会让传感器成像
  失效——同一 fprintd 进程内第一次 claim 能采图，之后每次 claim 都是均匀
  all-0xFF 帧、永远检测不到手指（上游 CAL_CHECK 恢复注释记录的 2026-09-15
  all-0xFF 即同一状态）。现在每次 claim 都执行完整链路：寄存器相位 → 读取
  → `97 00 00` 复位 → 上传。
- **F1r2 —— 上一会话校准块收养 + 延长重读阶梯**：会话收尾后固件要用数秒
  重建校准 RAM，最初几次读取全是零块。现在被丢弃的会话块会存入 stash 并
  作为恢复阶梯的收养来源（与 Windows 主机侧缓存同型），耐心 1 Hz 重读
  预算由 7 提至 20 次。这拯救了没有模板内嵌副本兜底的动作——尤其是
  enroll，此前会以 "broken calibration block, retry later" 失败并且
  旧指纹已被删除。

真机验证环境：**Acer Swift SF314-42**（V1.11，EgisTec EH575 1c7a:0575）、
**Fedora 44**、内核 6.19.10-300.fc44.x86_64、fprintd 1.94.5：指纹登录、
同一 fprintd 进程内连续验证（每次 claim 均匹配，包括第二次与第三次）、
会话后立即完整 12 阶段重录（经上一会话块收养恢复）、以及会话后校准
失效场景下的 enroll/verify。

## 状态（2026-09-13）

- **驱动已可用**：press 采集架构 + Windows 引擎 matcher 移植，真机
  （KDE 锁屏 / fprintd / Bitwarden polkit 解锁）验证通过；匹配器验证
  数字（小样本单机：离线 6 同人/12 异人 FRR/FAR 0%，真机冒充分离余量
  47——重标定后（阈值 335 vs 峰值 288）；修复前旧引擎为 15，已作废）见
  [comparison §6/§9](docs/comparison.md#6-windows-引擎移植终局方案)
- **v0.2.1 优化**：录入同点重复拒绝（Windows HIGHLY_SIMILARITY 移植，
  阈值 650 真机验证拦截精准）、校准块跨 close 主机缓存（Windows 同型）、
  两档空闲轮询（230/500ms）
- **master 未发布**：解锁时延压缩（verify/enroll 动作开始/手指事件后 15s 内
  120ms 快速轮询 + 按压稳定窗 400→250ms）、验证模板回馈（Windows 'AE' blob 的内存版：
  高置信匹配帧回授模板库，进程生命周期内越用越贴合，
  [comparison §6](docs/comparison.md#与-windows-原版的差异)）、
  模板 v2 内嵌校准块（传感器侧读数失效时上传模板内副本瞬时恢复，见
  [protocol §8 第 3 条](docs/protocol.md#8-已知陷阱全部真机验证2026-09-1213)；
  **建议重录指纹获得 v2 模板**，v1 模板仍可正常验证）
- **待办**：扩样本调优阈值、多机型反馈、上游化补丁

## 文档导航

按问题找章节（双语对照的总索引见 [docs/README.md](docs/README.md)）：

| 想了解 | 去处 |
|---|---|
| 安装/构建依赖了什么 | 本页 [目录结构](#目录结构) · [复现研究流程](#复现研究流程) |
| USB 通信协议与命令语义（CET300 命令集、初始化序列、未解项） | [protocol §2 命令与响应格式](docs/protocol.md#2-命令与响应格式) · [§4 初始化序列](docs/protocol.md#4-初始化序列) · [§10 尚未逆向的部分](docs/protocol.md#10-尚未逆向的部分) |
| 为什么 swipe/NCC/Bozorth3/SigFM 全不行 | [comparison §5 匹配器实验史：七个方案为何全败](docs/comparison.md#5-匹配器实验史七个方案为何全败2026-09-12) |
| 匹配器从哪来、系数提取与验证数字 | [windows-engine-tables](docs/windows-engine-tables.md) · [comparison §6 Windows 引擎移植](docs/comparison.md#6-windows-引擎移植终局方案) |
| Windows 怎么做录入（同点拒绝的出处） | [windows-enrollment](docs/windows-enrollment.md) |
| Windows 实际怎么用传感器（校准缓存、占空比） | protocol §4C 会话实际序列 · §7 在线行为实证（[docs/protocol.md](docs/protocol.md)） |
| 稳定性：陷阱清单、看门狗、挂死恢复 | [protocol §8 已知陷阱](docs/protocol.md#8-已知陷阱全部真机验证2026-09-1213) · [comparison §7 稳定性工程](docs/comparison.md#7-稳定性工程成果全部真机验证) |
| 录入相似阈值怎么标定 | [enroll-sim-calibration.txt](docs/enroll-sim-calibration.txt) · [calibrate-enroll-sim.py](scripts/calibrate-enroll-sim.py) |
| 优化路线与已完成项 | [optimization-plan.md](docs/optimization-plan.md) |

## 关键结论速查

1. EH575 是**图像传感器**（103×52 小图、主机侧匹配，**无死区列**），
   不是 match-on-chip（几何定案见 [protocol §3](docs/protocol.md#3-图像几何已定案)）
2. swipe+Bozorth3（topni1 驱动）是精度差的根源；经典匹配方案（NCC/
   Bozorth3/POC/SigFM/方向场）在本传感器原始信噪比下**全部**无法区分
   同人不同指（[comparison §5](docs/comparison.md#5-匹配器实验史七个方案为何全败2026-09-12)）
3. 本驱动 = EH577 的 press 采集架构 + topni1 校准初始化（EH575 出图
   必要条件）+ **Windows 引擎 matcher 移植**（11 取向脊线滤波器组 +
   512bit 描述子 + 海明/平移簇评分，系数提取自 vendor DLL；小样本
   离线 FRR/FAR 0%，真机集成验收通过，见
   [comparison §6](docs/comparison.md#6-windows-引擎移植终局方案)）
4. `01 01 01 → 重跑 PRE_INIT` 是 EH575 的本义错误处理
   （[protocol §4B](docs/protocol.md#4-初始化序列)）
5. 早前记录的 topni1 `FPI_DEVICE_Egis0575` 笔误经全历史复核**不存在**
   （[comparison §8](docs/comparison.md#8-已发现的上游问题)），无需回报

## 复现研究流程

```bash
# 0) 一次性：clone 本仓库并构建（驱动源码已在树内 libfprint/）
#    （需要 meson≥0.62 + ninja，以及 glib2/libusb/libgusb/pixman/openssl/
#     libgudev 的开发包；Arch 上再加 gobject-introspection、gtk-doc、glib2-devel）
git clone https://github.com/cosct/libfprint-egis0575 && cd libfprint-egis0575
meson setup libfprint/builddir libfprint
meson compile -C libfprint/builddir

# 1) 一次性：装临时 udev 规则获得设备直连权限（要 sudo 密码）
./scripts/setup-access.sh

# 2) 无手指探测 20s：验证初始化稳定、背景预热完成、空轮询无超时
./scripts/probe.sh

# 3) 采数据集：按脚本提示按压（先空 3 秒做背景预热）
./scripts/collect-dataset.sh press-test 60

# 4) 列活跃度分析（已定案：103 列全活跃、无死区；脚本供新机型复核）
python3 scripts/analyze-columns.py datasets/press-test-*/
```

Python 脚本依赖见 `requirements.txt`（Python ≥ 3.9 + numpy；
egis_matcher.py 的特征提取与 eval_sigfm 需 OpenCV，hwpoll 另需 pyusb）。本仓库（文档/脚本/工具）与驱动同样
按 LGPL-2.1-or-later 授权（见 `LICENSE`）。

### 驱动可调环境变量

- `EGIS0575_ACTIVE_WIDTH` — 有效列数（默认 103；已定案无死区，仅供实验）
- `EGIS0575_SKIP_CALIBRATION=1` — 跳过校准上传走 EH577 式初始化（已知会全零帧，仅 A/B 用）
- `EGIS0575_PGM_DEBUG_DIR` / `_LOG` / `_INTERVAL_MS` / `_CONTROL` — PGM 数据集采集
  （采集模式下驱动持续转储处理帧，enroll/verify 等动作不会完成——仅供
  无状态探测采集，配合 `_CONTROL` 指向的控制文件可暂停/恢复）
- `EGIS0575_FRAME_DUMP_DIR` — 原始 5356 字节帧转储
- `EGIS0575_LIVE_FRAME_PATH` — 实时帧写单个 PGM（看图用）
- `EGIS0575_VERIFY_DUMP_DIR` — 验证时转储 probe 与模板库特征数日志（离线匹配分析）
- `EGIS0575_DISABLE_STRETCH=1` — 关闭 stretch5 对比度增强
- `EGIS0575_ENROLL_SIM_THRESHOLD` — 录入同点重复拒绝阈值（默认 650；
  0 关闭。标定见 [enroll-sim-calibration.txt](docs/enroll-sim-calibration.txt)）
- `EGIS0575_FINGER_SETTLE_MS` — 按压稳定窗（默认 250ms；调小解锁更快但
  不稳定帧更多，A/B 用）
- `EGIS0575_VERIFY_FEEDBACK=0` — 关闭验证模板回馈（默认开：高置信匹配帧
  回授内存模板库，随 fprintd 进程生命周期有效；让 fprintd 常驻可跨会话
  保留——写 `/etc/systemd/system/fprintd.service.d/keepalive.conf`：
  `[Service]` 段下先 `ExecStart=`（置空）再 `ExecStart=/usr/lib/fprintd -t`，
  然后 `systemctl daemon-reload`；代价是传感器 24h 低速轮询，由健康看门狗兜底）
- `EGIS0575_DEBUG_MAX_FILES` — PGM/原始帧转储的文件数上限（默认 5000，
  约 26 MB 原始帧；所有调试转储均为 0600 权限、目录 0700，因其含
  生物特征数据）

## 目录结构

```
docs/     文档索引见 docs/README.md（中英双语，按板块组织）
libfprint/ 驱动源码（git subtree：upstream libfprint 完整历史 + egis0575
          驱动，LGPL-2.1+）；构建目录 builddir/ 不入库
scripts/  测试与数据采集工具（probe / 采集 / 分析 / 标定）
tools/    评测小工具（egis0575-matcher-test / egis0575-feedback-eval /
          eval_bz3 三个 C 工具 make 构建；hwpoll 为 Python 脚本）
packaging/ 发布打包配置：aur/PKGBUILD（AUR 版本的权威来源）· deb/build-deb.sh ·
          rpm/libfprint-egis0575.spec —— release workflow 在打
          egis0575-v* 标签时调用，产物上传至 GitHub Release 并自动更新 AUR
PKGBUILD  本地开发打包（从工作树构建；AUR 版本见 AUR 仓库）
```

不随仓库分发的内容（体积或隐私原因）：`refs/`（六份第三方参考实现，自行
clone）、`datasets/`（指纹原始帧，生物特征数据）、`acerdrv/`（Acer 官方
Windows 驱动，版权归 EgisTec/Acer）。
