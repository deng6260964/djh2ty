<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiService from '@/services/api'
import { showToast } from 'vant'

const router = useRouter()
const students = ref<any[]>([])
const loading = ref(false)
const showDetailDialog = ref(false)
const currentStudent = ref<any>({})
const studentProgress = ref<any>({})
const searchValue = ref('')
const activeTab = ref('list')

onMounted(() => {
  loadStudents()
})

const loadStudents = async () => {
  try {
    loading.value = true
    const response = await apiService.getStudents()
    students.value = response.data
  } catch (error) {
    showToast('加载学生列表失败')
  } finally {
    loading.value = false
  }
}

const openDetailDialog = async (student: any) => {
  currentStudent.value = student
  try {
    // 获取学生学习进度
    const response = await apiService.getStudentProgress(student.id)
    studentProgress.value = response.data
    showDetailDialog.value = true
  } catch (error) {
    showToast('加载学生详情失败')
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
</script>

<template>
  <div class="student-management">
    <!-- 头部导航 -->
    <van-nav-bar title="学生管理" left-arrow @click-left="goBack" />

    <!-- 标签页 -->
    <van-tabs v-model:active="activeTab">
      <van-tab title="学生列表" name="list">
        <div class="content">
          <!-- 搜索框 -->
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