SyzMini Weekly Check 代码补丁说明
================================

目标仓库：Cenginnn/Optimizing-Input-Minimization-in-Kernel-Fuzzing-SyzMini-
补丁文件：weekly-check.patch

本补丁包含：
1. syz-manager 加载影响矩阵时检查文件读取错误、矩阵维度和值域。
2. 新增 Manager 矩阵加载测试。
3. Target 增加 ValidateInfluenceMatrix / MergeInfluenceMatrix。
4. 修正静态影响关系 pair 数量统计。
5. Fuzzer 接收 Manager 的矩阵后，真正合并至 Target.InfluenceMatrix。
6. 增加调用级/参数级最小化执行次数的独立 named stats，使用 Fuzzer 现有 stats slice 避免 32 位平台上新增 uint64 字段的对齐风险。
7. 修复 removeCalls BFS 节点重复入队的问题。
8. 新增 prog 矩阵验证与合并测试。

重要说明：
- 本补丁没有改动 syzmini/syz-manager/stats.go。现有 Stats.mergeNamed 和 Stats.all
  已经可以累积并展示通过 Poll 发送来的命名统计字段，因此不必为了新增两个 named
  stats 而改该文件。
- exec minimize call / exec minimize arg 是最小化执行次数的分类计数；原有
  StatMinimize 仍然作为总最小化执行次数来源。新增分类值通过 StatMinimizeCall / StatMinimizeArg 单独统计，并在 execTotal 本地计数时排除，避免重复计算。
- README、.gitignore、configs、scripts、experiments 是本周建议的文档/实验文件，未放入
  此补丁，避免在未掌握你们本地文件内容时覆盖现有资料。

应用前：
1. 在仓库根目录执行 git status，确保已有工作已保存。
2. 确认当前代码仍与 GitHub main 上对应版本一致。
3. 执行 git apply --check weekly-check.patch 检查补丁。
4. 通过后执行 git apply weekly-check.patch。

应用后：
cd syzmini
gofmt -w prog/target.go prog/influence_test.go prog/minimization.go \
  syz-manager/manager.go syz-manager/influence_test.go \
  syz-fuzzer/fuzzer.go syz-fuzzer/proc.go

go test ./prog ./syz-manager ./syz-fuzzer
make

如 go test 或 make 出错，先不要直接 push；保留完整错误输出并修复。
