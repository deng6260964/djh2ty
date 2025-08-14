<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiService from '@/services/api'
import { showToast } from 'vant'

const router = useRouter()
const students = ref<any[]>([])
const loading = ref(false)
const showDetailDialog = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const currentStudent = ref<any>({})
const studentProgress = ref<any>({})
const searchValue = ref('')
const activeTab = ref('list')
const creating = ref(false)
const editing = ref(false)
const deleting = ref(false)

// 新增学生表单数据
const createForm = ref({
  name: '',
  phone: '',
  password: '',
  email: ''
})

// 编辑学生表单数据
const editForm = ref({
  name: '',
  phone: '',
  email: ''
})

onMounted(() => {
  loadStudents()
})

const loadStudents = async () => {
  try {
    loading.value = true
    console.log('开始加载学生列表...')
    
    const response = await apiService.getStudents()
    console.log('学生列表API响应:', response)
    
    if (response.success) {
      // 处理分页数据结构
      if (response.data && response.data.students) {
        students.value = response.data.students
      } else if (Array.isArray(response.data)) {
        students.value = response.data
      } else {
        students.value = []
      }
      console.log('学生列表加载成功，共', students.value.length, '个学生')
    } else {
      console.error('学生列表加载失败:', response.message)
      showToast({ type: 'fail', message: response.message || '加载学生列表失败' })
      students.value = []
    }
  } catch (error: any) {
    console.error('加载学生列表失败:', error)
    showToast({ type: 'fail', message: error.response?.data?.message || '加载学生列表失败' })
    students.value = []
  } finally {
    loading.value = false
  }
}

const openDetailDialog = async (student: any) => {
  currentStudent.value = student
  try {
    console.log('开始加载学生详情，学生ID:', student.id)
    
    // 检查学生ID是否有效
    if (!student.id) {
      console.error('学生ID无效:', student)
      showToast({ type: 'fail', message: '学生ID无效' })
      return
    }
    
    // 获取学生学习进度
    const response = await apiService.getStudentProgress(student.id)
    console.log('学生进度API响应:', response)
    
    if (response.success) {
      studentProgress.value = response.data
      showDetailDialog.value = true
      console.log('学生详情加载成功')
    } else {
      console.error('学生进度API返回失败:', response.message)
      showToast({ type: 'fail', message: response.message || '加载学生详情失败' })
    }
  } catch (error: any) {
    console.error('加载学生详情失败:', error)
    showToast({ type: 'fail', message: error.response?.data?.message || '加载学生详情失败' })
  }
}

const filteredStudents = () => {
  if (!searchValue.value) {
    return students.value
  }
  return students.value.filter(student => 
    student.name.toLowerCase().includes(searchValue.value.toLowerCase()) ||
    student.phone.includes(searchValue.value)
  )
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const getStudentStats = () => {
  const totalStudents = students.value.length
  const activeStudents = students.value.filter(s => s.last_login && 
    new Date(s.last_login) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
  ).length
  
  return {
    total: totalStudents,
    active: activeStudents,
    inactive: totalStudents - activeStudents
  }
}

const getAverageScore = () => {
  const studentsWithScores = students.value.filter(s => s.average_score !== null)
  if (studentsWithScores.length === 0) return 0
  
  const totalScore = studentsWithScores.reduce((sum, s) => sum + s.average_score, 0)
  return Math.round(totalScore / studentsWithScores.length)
}

const getTopStudents = () => {
  return students.value
    .filter(s => s.average_score !== null)
    .sort((a, b) => b.average_score - a.average_score)
    .slice(0, 10)
}

const goBack = () => {
  router.back()
}

// 打开新增学生对话框
const openCreateDialog = () => {
  createForm.value = {
    name: '',
    phone: '',
    password: '',
    email: ''
  }
  showCreateDialog.value = true
}

// 创建学生
const createStudent = async () => {
  try {
    creating.value = true
    showToast({ type: 'loading', message: '创建中...', duration: 0 })
    
    console.log('开始创建学生，表单数据:', createForm.value)
    
    // 验证表单
    if (!createForm.value.name || !createForm.value.phone || !createForm.value.password) {
      console.error('表单验证失败：缺少必填字段')
      showToast({ type: 'fail', message: '请填写必填字段' })
      return
    }
    
    // 验证手机号格式
    const phoneRegex = /^1[3-9]\d{9}$/
    if (!phoneRegex.test(createForm.value.phone)) {
      console.error('手机号格式验证失败:', createForm.value.phone)
      showToast({ type: 'fail', message: '请输入正确的手机号' })
      return
    }
    
    // 验证密码长度
    if (createForm.value.password.length < 6) {
      console.error('密码长度验证失败:', createForm.value.password.length)
      showToast({ type: 'fail', message: '密码长度不能少于6位' })
      return
    }
    
    const response = await apiService.createStudent(createForm.value)
    console.log('创建学生API响应:', response)
    
    if (response.success) {
      console.log('学生创建成功')
      showToast({ type: 'success', message: '学生创建成功' })
      showCreateDialog.value = false
      loadStudents() // 重新加载学生列表
    } else {
      console.error('创建学生API返回失败:', response.message)
      showToast({ type: 'fail', message: response.message || '创建学生失败' })
    }
  } catch (error: any) {
    console.error('创建学生失败:', error)
    showToast({ type: 'fail', message: error.response?.data?.message || '创建学生失败' })
  } finally {
    creating.value = false
  }
}

// 打开编辑学生对话框
const openEditDialog = (student: any) => {
  currentStudent.value = student
  editForm.value = {
    name: student.name,
    phone: student.phone,
    email: student.email || ''
  }
  showEditDialog.value = true
}

// 更新学生信息
const updateStudent = async () => {
  try {
    editing.value = true
    showToast({ type: 'loading', message: '更新中...', duration: 0 })
    
    console.log('开始更新学生信息，学生ID:', currentStudent.value.id, '表单数据:', editForm.value)
    
    // 检查学生ID是否有效
    if (!currentStudent.value.id) {
      console.error('学生ID无效:', currentStudent.value)
      showToast({ type: 'fail', message: '学生ID无效' })
      return
    }
    
    // 验证表单
    if (!editForm.value.name || !editForm.value.phone) {
      console.error('表单验证失败：缺少必填字段')
      showToast({ type: 'fail', message: '请填写必填字段' })
      return
    }
    
    // 验证手机号格式
    const phoneRegex = /^1[3-9]\d{9}$/
    if (!phoneRegex.test(editForm.value.phone)) {
      console.error('手机号格式验证失败:', editForm.value.phone)
      showToast({ type: 'fail', message: '请输入正确的手机号' })
      return
    }
    
    const response = await apiService.updateStudent(currentStudent.value.id, editForm.value)
    console.log('更新学生API响应:', response)
    
    if (response.success) {
      console.log('学生信息更新成功')
      showToast({ type: 'success', message: '学生信息更新成功' })
      showEditDialog.value = false
      loadStudents() // 重新加载学生列表
    } else {
      console.error('更新学生API返回失败:', response.message)
      showToast({ type: 'fail', message: response.message || '更新学生信息失败' })
    }
  } catch (error: any) {
    console.error('更新学生信息失败:', error)
    showToast({ type: 'fail', message: error.response?.data?.message || '更新学生信息失败' })
  } finally {
    editing.value = false
  }
}

// 删除学生
const deleteStudent = async (student: any) => {
  try {
    // 使用原生确认对话框
    const confirmed = confirm(`确定要删除学生 "${student.name}" 吗？\n\n此操作不可恢复！`)
    
    if (!confirmed) return
    
    deleting.value = true
    showToast({ type: 'loading', message: '删除中...', duration: 0 })
    
    const response = await apiService.deleteStudent(student.id)
    
    if (response.success) {
      showToast({ type: 'success', message: '学生删除成功' })
      loadStudents() // 重新加载学生列表
    } else {
      showToast({ type: 'fail', message: response.message || '删除学生失败' })
    }
  } catch (error: any) {
    console.error('删除学生失败:', error)
    showToast({ type: 'fail', message: error.response?.data?.message || '删除学生失败' })
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="student-management">
    <!-- 头部导航 -->
    <van-nav-bar title="学生管理" left-arrow @click-left="goBack" />

    <!-- 标签页 -->
    <van-tabs v-model:active="activeTab">
      <van-tab title="学生列表" name="list">
        <div class="content">
          <!-- 搜索框和操作按钮 -->
          <div class="search-section">
            <van-search
              v-model="searchValue"
              placeholder="搜索学生姓名或手机号"
              show-action
            >
              <template #action>
                <div @click="searchValue = ''">清空</div>
              </template>
            </van-search>
            
            <!-- 新增学生按钮 -->
            <div class="action-buttons">
              <van-button type="primary" size="small" @click="openCreateDialog">
                <van-icon name="plus" /> 新增学生
              </van-button>
            </div>
          </div>

          <!-- 学生列表 -->
          <van-pull-refresh v-model="loading" @refresh="loadStudents">
            <van-list>
              <van-card
                v-for="student in filteredStudents()"
                :key="student.id"
                :title="student.name"
                class="student-card"
                @click="openDetailDialog(student)"
              >
                <template #desc>
                  <div class="student-info">
                    <div>手机号: {{ student.phone }}</div>
                    <div v-if="student.average_score !== null">
                      平均分: {{ student.average_score }}分
                    </div>
                    <div v-if="student.last_login">
                      最后登录: {{ formatDate(student.last_login) }}
                    </div>
                  </div>
                </template>
                
                <template #tags>
                  <van-tag 
                    :type="student.last_login && new Date(student.last_login) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) ? 'success' : 'default'"
                  >
                    {{ student.last_login && new Date(student.last_login) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) ? '活跃' : '不活跃' }}
                  </van-tag>
                  <van-tag v-if="student.average_score >= 90" type="success" class="ml-1">
                    优秀
                  </van-tag>
                  <van-tag v-else-if="student.average_score >= 80" type="primary" class="ml-1">
                    良好
                  </van-tag>
                  <van-tag v-else-if="student.average_score >= 60" type="warning" class="ml-1">
                    及格
                  </van-tag>
                  <van-tag v-else-if="student.average_score !== null" type="danger" class="ml-1">
                    待提高
                  </van-tag>
                </template>
                
                <template #footer>
                  <div class="student-actions">
                    <van-button size="small" type="primary" @click.stop="openDetailDialog(student)">
                      查看详情
                    </van-button>
                    <van-button size="small" type="default" @click.stop="openEditDialog(student)">
                      编辑
                    </van-button>
                    <van-button size="small" type="danger" @click.stop="deleteStudent(student)" :loading="deleting">
                      删除
                    </van-button>
                  </div>
                </template>
              </van-card>
            </van-list>
          </van-pull-refresh>

          <!-- 空状态 -->
          <van-empty v-if="!loading && filteredStudents().length === 0" description="暂无学生数据" />
        </div>
      </van-tab>
      
      <van-tab title="数据统计" name="stats">
        <div class="content">
          <!-- 统计卡片 -->
          <div class="stats-cards">
            <van-grid :column-num="2" :border="false">
              <van-grid-item>
                <div class="stat-card">
                  <div class="stat-number">{{ getStudentStats().total }}</div>
                  <div class="stat-label">学生总数</div>
                </div>
              </van-grid-item>
              
              <van-grid-item>
                <div class="stat-card">
                  <div class="stat-number">{{ getStudentStats().active }}</div>
                  <div class="stat-label">活跃学生</div>
                </div>
              </van-grid-item>
              
              <van-grid-item>
                <div class="stat-card">
                  <div class="stat-number">{{ getAverageScore() }}</div>
                  <div class="stat-label">平均分</div>
                </div>
              </van-grid-item>
              
              <van-grid-item>
                <div class="stat-card">
                  <div class="stat-number">{{ getStudentStats().inactive }}</div>
                  <div class="stat-label">不活跃学生</div>
                </div>
              </van-grid-item>
            </van-grid>
          </div>

          <!-- 优秀学生排行 -->
          <div class="top-students">
            <van-cell-group>
              <van-cell title="优秀学生排行榜" />
              <van-cell
                v-for="(student, index) in getTopStudents()"
                :key="student.id"
                :title="`${index + 1}. ${student.name}`"
                :value="`${student.average_score}分`"
                @click="openDetailDialog(student)"
              >
                <template #icon>
                  <van-icon 
                    v-if="index < 3" 
                    :name="index === 0 ? 'medal-o' : index === 1 ? 'medal' : 'award-o'" 
                    :color="index === 0 ? '#FFD700' : index === 1 ? '#C0C0C0' : '#CD7F32'"
                    size="16"
                  />
                </template>
              </van-cell>
            </van-cell-group>
          </div>
        </div>
      </van-tab>
    </van-tabs>

    <!-- 学生详情弹窗 -->
    <van-dialog
      v-model:show="showDetailDialog"
      :title="currentStudent.name + ' - 详细信息'"
      class="detail-dialog"
    >
      <div class="detail-content">
        <van-tabs>
          <van-tab title="基本信息">
            <div class="basic-info">
              <van-cell title="姓名" :value="currentStudent.name" />
              <van-cell title="手机号" :value="currentStudent.phone" />
              <van-cell title="注册时间" :value="formatDate(currentStudent.created_at)" />
              <van-cell title="最后登录" :value="currentStudent.last_login ? formatDate(currentStudent.last_login) : '从未登录'" />
              <van-cell title="平均分" :value="currentStudent.average_score !== null ? currentStudent.average_score + '分' : '暂无成绩'" />
            </div>
          </van-tab>
          
          <van-tab title="学习进度">
            <div class="progress-info">
              <van-cell title="已完成课程" :value="studentProgress.completed_courses || 0" />
              <van-cell title="已提交作业" :value="studentProgress.submitted_homeworks || 0" />
              <van-cell title="已参加考试" :value="studentProgress.completed_exams || 0" />
              <van-cell title="学习天数" :value="studentProgress.study_days || 0" />
              <van-cell title="总学习时长" :value="(studentProgress.total_study_time || 0) + '小时'" />
            </div>
          </van-tab>
          
          <van-tab title="成绩分析">
            <div class="score-analysis">
              <van-cell title="作业平均分" :value="studentProgress.homework_avg_score ? studentProgress.homework_avg_score + '分' : '暂无'" />
              <van-cell title="考试平均分" :value="studentProgress.exam_avg_score ? studentProgress.exam_avg_score + '分' : '暂无'" />
              <van-cell title="最高分" :value="studentProgress.highest_score ? studentProgress.highest_score + '分' : '暂无'" />
              <van-cell title="最低分" :value="studentProgress.lowest_score ? studentProgress.lowest_score + '分' : '暂无'" />
              
              <!-- 成绩趋势 -->
              <div v-if="studentProgress.score_trend && studentProgress.score_trend.length > 0" class="score-trend">
                <van-cell title="成绩趋势" />
                <div class="trend-chart">
                  <div 
                    v-for="(score, index) in studentProgress.score_trend.slice(-10)" 
                    :key="index" 
                    class="trend-bar"
                    :style="{ height: (score / 100) * 60 + 'px' }"
                  >
                    <span class="trend-score">{{ score }}</span>
                  </div>
                </div>
              </div>
            </div>
          </van-tab>
          
          <van-tab title="最近活动">
            <div class="recent-activities">
              <van-cell
                v-for="activity in studentProgress.recent_activities || []"
                :key="activity.id"
                :title="activity.title"
                :label="formatDate(activity.created_at)"
                :value="activity.type === 'homework' ? '作业' : activity.type === 'exam' ? '考试' : '课程'"
              />
              
              <van-empty v-if="!studentProgress.recent_activities || studentProgress.recent_activities.length === 0" description="暂无活动记录" />
            </div>
          </van-tab>
        </van-tabs>
      </div>
    </van-dialog>

    <!-- 新增学生对话框 -->
    <van-dialog
      v-model:show="showCreateDialog"
      title="新增学生"
      show-cancel-button
      :before-close="() => !creating"
      @confirm="createStudent"
      :confirm-button-loading="creating"
      confirm-button-text="创建"
    >
      <div class="form-content">
        <van-form>
          <van-field
            v-model="createForm.name"
            label="姓名"
            placeholder="请输入学生姓名"
            required
            :rules="[{ required: true, message: '请输入学生姓名' }]"
          />
          <van-field
            v-model="createForm.phone"
            label="手机号"
            placeholder="请输入手机号"
            type="tel"
            required
            :rules="[
              { required: true, message: '请输入手机号' },
              { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' }
            ]"
          />
          <van-field
            v-model="createForm.password"
            label="密码"
            placeholder="请输入密码（至少6位）"
            type="password"
            required
            :rules="[
              { required: true, message: '请输入密码' },
              { validator: (value: string) => value.length >= 6, message: '密码长度不能少于6位' }
            ]"
          />
          <van-field
            v-model="createForm.email"
            label="邮箱"
            placeholder="请输入邮箱（可选）"
            type="email"
          />
        </van-form>
      </div>
    </van-dialog>

    <!-- 编辑学生对话框 -->
    <van-dialog
      v-model:show="showEditDialog"
      title="编辑学生信息"
      show-cancel-button
      :before-close="() => !editing"
      @confirm="updateStudent"
      :confirm-button-loading="editing"
      confirm-button-text="保存"
    >
      <div class="form-content">
        <van-form>
          <van-field
            v-model="editForm.name"
            label="姓名"
            placeholder="请输入学生姓名"
            required
            :rules="[{ required: true, message: '请输入学生姓名' }]"
          />
          <van-field
            v-model="editForm.phone"
            label="手机号"
            placeholder="请输入手机号"
            type="tel"
            required
            :rules="[
              { required: true, message: '请输入手机号' },
              { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' }
            ]"
          />
          <van-field
            v-model="editForm.email"
            label="邮箱"
            placeholder="请输入邮箱（可选）"
            type="email"
          />
        </van-form>
      </div>
    </van-dialog>
  </div>
</template>

<style scoped>
.student-management {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.content {
  padding: 16px;
}

.search-section {
  margin-bottom: 16px;
}

.action-buttons {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.action-buttons .van-button {
  margin-left: 8px;
}

.form-content {
  padding: 16px 0;
}

.form-content .van-field {
  margin-bottom: 12px;
}

.student-card {
  margin-bottom: 16px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}

.student-info {
  font-size: 14px;
  color: #666;
  line-height: 1.4;
}

.student-actions {
  display: flex;
  gap: 8px;
}

.stats-cards {
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
  color: #1989fa;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.top-students {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.detail-content {
  max-height: 70vh;
  overflow-y: auto;
}

.basic-info, .progress-info, .score-analysis, .recent-activities {
  padding: 16px 0;
}

.score-trend {
  padding: 16px;
}

.trend-chart {
  display: flex;
  align-items: end;
  gap: 4px;
  height: 80px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-top: 8px;
}

.trend-bar {
  flex: 1;
  background: linear-gradient(to top, #1989fa, #64b5f6);
  border-radius: 2px;
  position: relative;
  min-height: 10px;
  display: flex;
  align-items: end;
  justify-content: center;
}

.trend-score {
  font-size: 10px;
  color: #fff;
  font-weight: 600;
  margin-bottom: 2px;
}

.ml-1 {
  margin-left: 4px;
}

:deep(.van-card__content) {
  padding: 16px;
}

:deep(.van-card__footer) {
  padding: 0 16px 16px;
}

:deep(.detail-dialog) {
  width: 95vw;
  max-width: 600px;
}

:deep(.detail-dialog .van-dialog__content) {
  padding: 0;
}

:deep(.van-grid-item__content) {
  padding: 8px;
}

:deep(.van-cell__title) {
  font-weight: 500;
}

:deep(.van-search__action) {
  color: #1989fa;
}
</style>