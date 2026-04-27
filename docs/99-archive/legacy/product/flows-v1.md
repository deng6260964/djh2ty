# 家教辅助系统 - 核心业务流程

> 状态：归档
> 范围：全项目
> 更新：2026-04-26
> 版本：1.0
> 日期：2026-02-27
> 说明：描述系统中 5 条核心业务流程，每条附文字说明和 Mermaid 流程图。

---

## 目录

1. [老师登录流程](#1-老师登录流程)
2. [排课并发送课程提醒通知流程](#2-排课并发送课程提醒通知流程)
3. [布置作业到学生查看流程](#3-布置作业到学生查看流程)
4. [收费记录流程](#4-收费记录流程)
5. [学生微信登录小程序流程](#5-学生微信登录小程序流程)

---

## 1. 老师登录流程

### 流程说明

老师通过管理端 Web 页面输入用户名和密码进行身份认证，系统校验后颁发 JWT Token，后续所有 API 请求携带该 Token 进行鉴权。Token 过期后自动跳回登录页，要求重新登录。

**参与方：** 老师（浏览器）、管理端前端、后端 API

**关键规则：**
- 密码在数据库中以 bcrypt 哈希存储，校验时对比哈希值
- 连续登录失败 5 次，账号锁定 15 分钟
- JWT Token 有效期 8 小时，前端在 localStorage 中持久化存储
- 所有受保护路由在请求前验证 Token 有效性，无效则跳转登录页

### 流程图

```mermaid
flowchart TD
    A([老师打开管理端]) --> B{本地 Token\n是否有效?}
    B -- 是 --> C([直接进入仪表盘])
    B -- 否/不存在 --> D[显示登录页面]

    D --> E[老师输入用户名和密码]
    E --> F[点击登录按钮]
    F --> G{前端表单校验\n字段是否为空?}
    G -- 有空字段 --> H[高亮提示必填字段]
    H --> E

    G -- 通过 --> I[前端发送 POST /api/auth/login]
    I --> J{后端：账号\n是否被锁定?}
    J -- 是 --> K[返回 429 Too Many Requests\n提示剩余锁定时间]
    K --> D

    J -- 否 --> L{后端：用户名\n是否存在?}
    L -- 否 --> M[失败次数 +1]
    M --> N{失败次数\n是否达到 5 次?}
    N -- 是 --> O[锁定账号 15 分钟\n返回错误提示]
    O --> D
    N -- 否 --> P[返回 401：用户名或密码错误]
    P --> D

    L -- 是 --> Q{后端：密码\nbcrypt 校验通过?}
    Q -- 否 --> M
    Q -- 是 --> R[重置失败次数\n生成 JWT Token\n有效期 8 小时]
    R --> S[返回 200 含 Token 和用户信息]
    S --> T[前端存储 Token\n到 localStorage]
    T --> C
```

---

## 2. 排课并发送课程提醒通知流程

### 流程说明

老师在管理端为指定学生创建一节课程，系统在保存前进行时间冲突检测。课程创建成功后，系统可在上课前预设时间（如 2 小时前）自动通过微信推送提醒通知给学生/家长。

**参与方：** 老师（管理端）、后端 API、数据库、微信服务（消息推送）

**关键规则：**
- 冲突检测：新课时间段 [start_time, end_time) 与已有 pending/completed 课程时间段有任何重叠视为冲突
- 课程状态默认为 pending（待上课）
- 提醒通知在课程开始前 X 小时（老师可配置，默认 2 小时）由后台定时任务触发
- 若学生/家长未绑定微信 OpenID，通知仅记录系统日志，不实际推送

### 流程图

```mermaid
flowchart TD
    A([老师进入课程管理页]) --> B[点击「新建课程」]
    B --> C[打开课程创建表单]
    C --> D[填写：学生/科目/日期/开始时间/时长/备注]
    D --> E[点击「保存」]

    E --> F{前端表单校验：\n必填字段是否完整?}
    F -- 有缺失 --> G[高亮缺失字段，阻止提交]
    G --> D

    F -- 通过 --> H[发送 POST /api/courses]

    H --> I{后端：查询数据库\n是否存在时间冲突?}
    I -- 冲突 --> J[返回 409 Conflict\n包含冲突课程的详情]
    J --> K[前端弹出冲突提示对话框\n显示冲突课程信息]
    K --> D

    I -- 无冲突 --> L[写入 courses 表\nstatus=pending]
    L --> M[返回 201 Created\n含课程 ID]
    M --> N[前端刷新日历/列表视图\n显示新课程]

    M --> O[后台创建定时提醒任务\n写入 notifications 表\nscheduled_at = start_time - 2h]

    subgraph 定时任务调度
        P([定时任务每分钟轮询]) --> Q{有 scheduled_at\n到达的 pending 通知?}
        Q -- 否 --> P
        Q -- 是 --> R{学生/家长\n已绑定微信 OpenID?}
        R -- 否 --> S[标记通知 send_status=failed\n写入日志]
        R -- 是 --> T[调用微信模板消息接口\n发送课程提醒]
        T --> U{发送成功?}
        U -- 否 --> V[send_status=failed\n记录错误日志]
        U -- 是 --> W[send_status=sent\n记录 send_at 时间]
    end

    O --> P
```

---

## 3. 布置作业到学生查看流程

### 流程说明

老师在管理端选择一个或多个学生，编写作业内容并发布。系统为每个学生创建独立的提交记录。学生在微信小程序端查看作业详情，完成后可提交。老师批改后，学生可在小程序端查看评分和评语。

**参与方：** 老师（管理端）、学生（微信小程序）、后端 API

**关键规则：**
- 同一份作业可同时布置给多个学生，系统为每个学生创建独立的 assignment_submissions 记录
- 作业内容使用富文本编辑器（ReactQuill），支持图文混合
- 小程序端使用 HTML 渲染组件显示富文本内容
- 截止日期过后未提交的作业，老师端显示红色逾期标识

### 流程图

```mermaid
flowchart TD
    subgraph 老师端-布置作业
        A([老师进入作业管理]) --> B[点击「布置作业」]
        B --> C[填写：标题/科目/截止日期]
        C --> D[富文本编辑器编写作业内容]
        D --> E[在学生选择器中勾选一个或多个学生]
        E --> F[点击「发布」]
        F --> G{前端校验：\n必填字段是否完整?}
        G -- 缺失 --> H[提示缺失字段]
        H --> C
        G -- 通过 --> I[POST /api/assignments\n含 student_ids 数组]
        I --> J[后端写入 assignments 表]
        J --> K[为每个 student_id\n写入 assignment_submissions 记录\nstatus=pending]
        K --> L[返回 201 Created]
        L --> M[前端刷新作业列表\n显示新作业及完成率 0/N]
    end

    subgraph 学生端-查看作业
        N([学生打开小程序「作业」Tab]) --> O[GET /api/student/assignments\n携带学生 Token]
        O --> P[后端查询该学生的 assignment_submissions\nstatus=pending]
        P --> Q[小程序渲染「待完成」作业列表]
        Q --> R[学生点击某条作业]
        R --> S[GET /api/student/assignments/:id]
        S --> T[渲染作业详情页\n富文本内容/截止日期]
    end

    subgraph 老师端-批改作业
        U([老师进入作业管理]) --> V[筛选「待批改」状态]
        V --> W[点击某学生的提交记录]
        W --> X[查看学生提交内容]
        X --> Y[输入评分 0-100 和评语]
        Y --> Z[点击「保存批改」]
        Z --> AA[PUT /api/assignments/:id/submissions/:sid\n含 score 和 comment]
        AA --> BB[后端更新 submission\nstatus=graded\n记录 graded_at]
        BB --> CC[返回 200 OK]
        CC --> DD[前端作业状态变为「已批改」]
    end

    subgraph 学生端-查看批改结果
        EE([学生切换到「已完成」Tab]) --> FF[列表显示已批改作业]
        FF --> GG[点击作业]
        GG --> HH[作业详情页显示：\n大号字体分数 + 富文本评语]
    end

    M --> N
    DD --> EE
```

---

## 4. 收费记录流程

### 流程说明

老师首先配置各科目的课时单价。每当一节课被标记为"已完成"后，系统自动根据课时时长和科目单价计算应收金额。老师收款后手动录入收款记录，系统实时更新欠费金额。老师可在收费报表中查看各学生的应收/已收/欠费情况。

**参与方：** 老师（管理端）、后端 API、数据库

**关键规则：**
- 应收金额基于"已完成"状态课程的累计计算，修改课程状态会触发重新计算
- 课时单价按科目维度设置，修改单价只影响未来课程（已结算的不回溯）
- 欠费 = 应收合计 - 已收合计，实时计算，不缓存
- 收款记录支持软删除（is_deleted=true），不物理删除，保证账单可追溯

### 流程图

```mermaid
flowchart TD
    subgraph 前置：设置科目单价
        A([老师进入收费管理-设置]) --> B[查看科目单价列表]
        B --> C{科目是否存在?}
        C -- 否 --> D[点击「添加科目」\n填写科目名和单价]
        D --> E[POST /api/billing/subjects]
        E --> F[保存科目单价配置]
        C -- 是 --> G[点击「编辑」修改单价]
        G --> H[PUT /api/billing/subjects/:id]
        H --> F
    end

    subgraph 触发应收：标记课程完成
        I([老师打开课程详情]) --> J[点击「标记为已完成」]
        J --> K[PUT /api/courses/:id\nstatus=completed]
        K --> L[后端更新课程状态]
        L --> M[应收金额实时重算\n= 该学生所有 completed 课程\n按科目匹配单价累加]
    end

    subgraph 录入收款记录
        N([老师收到学生付款]) --> O[进入收费管理-该学生账单页]
        O --> P[查看「应收 / 已收 / 欠费」摘要]
        P --> Q[点击「录入收款」]
        Q --> R[填写：收款金额/日期/支付方式/备注]
        R --> S[POST /api/billing/records]
        S --> T[写入 billing_records 表]
        T --> U[实时重算欠费金额\n= 应收合计 - 已收合计]
        U --> V[页面更新：欠费金额减少]
    end

    subgraph 查看收费报表
        W([老师进入收费管理-报表]) --> X[选择时间范围\n或学生筛选]
        X --> Y[GET /api/billing/report\n含筛选参数]
        Y --> Z[后端聚合计算\n应收/已收/欠费汇总]
        Z --> AA[展示报表：\n各学生明细 + 总计]
        AA --> AB{有欠费学生?}
        AB -- 是 --> AC[欠费学生高亮红色显示\n可点击「发送欠费提醒」]
        AC --> AD[POST /api/notifications\ntype=overdue_fee]
        AD --> AE[微信推送欠费提醒给家长]
        AB -- 否 --> AF([结束])
    end

    F --> I
    M --> N
    V --> W
```

---

## 5. 学生微信登录小程序流程

### 流程说明

学生（或家长）首次打开微信小程序时，通过微信授权获取临时 code，后端使用该 code 向微信服务器换取 OpenID，再与系统中的学生档案进行绑定，完成登录。登录成功后颁发 JWT Token，后续请求携带 Token 免登录访问。

**参与方：** 学生/家长（微信小程序）、微信服务器、后端 API、数据库

**关键规则：**
- 微信 OpenID 全局唯一且不变，是身份识别的核心标识
- 首次登录时，若老师尚未在学生档案中绑定该微信号，登录失败，引导学生联系老师
- 老师可在管理端为学生档案填写 wechat_openid（通过手机号匹配或手动录入）
- Token 有效期 7 天（小程序端使用习惯，比 Web 端更长）
- Token 存储在小程序的 wx.setStorageSync，下次启动时读取验证

### 流程图

```mermaid
flowchart TD
    A([学生打开微信小程序]) --> B{本地 Storage\n是否有有效 Token?}
    B -- 是 --> C[GET /api/student/me 验证 Token]
    C --> D{Token 有效?}
    D -- 是 --> E([直接进入首页])
    D -- 否/过期 --> F[清除本地 Token\n跳转登录页]

    B -- 否/不存在 --> F

    F --> G[显示登录页面\n「微信一键登录」按钮]
    G --> H[用户点击「微信登录」]
    H --> I[调用 wx.login\n获取临时 code]
    I --> J{code 获取成功?}
    J -- 否 --> K[提示「微信登录失败，请重试」]
    K --> G

    J -- 是 --> L[POST /api/auth/wechat-login\n携带 code]
    L --> M[后端调用微信接口:\nGET https://api.weixin.qq.com/sns/jscode2session\n换取 openid + session_key]
    M --> N{微信接口返回成功?}
    N -- 否 --> O[返回 502 微信服务异常\n前端提示重试]
    O --> G

    N -- 是 --> P{数据库查询:\n该 openid 是否已绑定学生档案?}
    P -- 否 --> Q[返回 403:\n「您的账号未绑定，请联系老师」]
    Q --> R[小程序显示引导提示页\n显示老师联系方式]

    P -- 是 --> S[查询学生信息及权限\n判断是学生还是家长]
    S --> T[生成 JWT Token\n有效期 7 天]
    T --> U[返回 200:\nToken + 用户基本信息]
    U --> V[小程序存储 Token\n到 wx.setStorageSync]
    V --> W[跳转到首页\n显示学生姓名和相关数据]

    subgraph 老师端-绑定微信号
        X([管理端：学生详情页]) --> Y[点击「绑定微信」]
        Y --> Z[填写学生微信号 或 让学生扫码绑定]
        Z --> AA[PUT /api/students/:id\n更新 wechat_openid]
        AA --> AB[绑定成功，下次学生登录即可正常进入]
    end
```

---

## 附录：各流程与接口对照

| 流程 | 主要接口 | 说明 |
|------|---------|------|
| 老师登录 | POST /api/auth/login | 账号密码换 JWT Token |
| 排课 | POST /api/courses | 含冲突检测逻辑 |
| 排课提醒 | POST /api/notifications（定时） | 由后台定时任务触发 |
| 布置作业 | POST /api/assignments | 批量为多学生创建 submission |
| 批改作业 | PUT /api/assignments/:id/submissions/:sid | 更新评分和评语 |
| 设置单价 | POST /api/billing/subjects | 科目单价配置 |
| 录入收款 | POST /api/billing/records | 实际收款记录 |
| 查看报表 | GET /api/billing/report | 聚合应收/已收/欠费 |
| 微信登录 | POST /api/auth/wechat-login | code → openid → JWT |
| 绑定微信 | PUT /api/students/:id | 更新 wechat_openid |

---

*文档结束*
