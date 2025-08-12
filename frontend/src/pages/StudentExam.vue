<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import apiService from '@/services/api'
import { showToast, showConfirmDialog } from 'vant'

const router = useRouter()
const exams = ref<any[]>([])
const loading = ref(false)
const showDetailDialog = ref(false)
const showExamDialog = ref(false)
const currentExam = ref<any>({})
const questions = ref<any[]>([])
const answers = ref<Record<string, any>>({})
const timeLeft = ref(0)
const timer = ref<NodeJS.Timeout | null>(null)
const activeTab = ref('available')

onMounted(() => {
  loadExams()
})

onUnmounted(() => {
  if (timer.value) {
    clearInterval(timer.value)
  }
})

const loadExams = async () => {
  try {
    loading.value = true
    const response = await apiService.getExams()
    exams.value = response.data
  } catch (error) {
    showToast('加载考试失败')
  } finally {
    loading.value = false
  }
}

const openDetailDialog = (exam: any) => {
  currentExam.value = exam
  showDetailDialog.value = true
}

const startExam = async () => {
  try {
    // 获取考试题目
    const questionPromises = currentExam.value.question_ids.map((id: string) => 
      apiService.getQuestion(parseInt(id))
    )
    const questionResponses = await Promise.all(questionPromises)
    questions.value = questionResponses.map(res => res.data)
    
    // 初始化答案
    answers.value = {}
    questions.value.forEach(q => {
      answers.value[q.id] = ''
    })
    
    // 设置考试时间
    timeLeft.value = currentExam.value.duration * 60 // 转换为秒
    startTimer()
    
    showDetailDialog.value = false
    showExamDialog.value = true
  } catch (error) {
    showToast('开始考试失败')
  }
}

const startTimer = () => {
  timer.value = setInterval(() => {
    timeLeft.value--
    if (timeLeft.value <= 0) {
      // 时间到，自动提交
      submitExam(true)
    }
  }, 1000)
}

const submitExam = async (autoSubmit = false) => {
  try {
    if (!autoSubmit) {
      await showConfirmDialog({
        title: '确认提交',
        message: '确定要提交考试吗？提交后将无法修改。',
      })
    }
    
    if (timer.value) {
      clearInterval(timer.value)
      timer.value = null
    }
    
    await apiService.submitExam(currentExam.value.id, {
      answers: answers.value
    })
    
    showToast(autoSubmit ? '考试时间到，已自动提交' : '提交考试成功')
    showExamDialog.value = false
    loadExams()
  } catch (error) {
    if (error !== 'cancel') {
      showToast('提交考试失败')
    }
  }
}

const formatTime = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const getExamStatus = (exam: any) => {
  const now = new Date()
  const startTime = new Date(exam.start_time)
  const endTime = new Date(exam.end_time)
  
  if (now < startTime) {
    return '未开始'
  } else if (now >= startTime && now <= endTime) {
    return '进行中'
  } else {
    return '已结束'
  }
}

const getStatusColor = (exam: any) => {
  const status = getExamStatus(exam)
  const colorMap: Record<string, string> = {
    '未开始': 'warning',
    '进行中': 'success',
    '已结束': 'default'
  }
  return colorMap[status] || 'default'
}

const canTakeExam = (exam: any) => {
  const status = getExamStatus(exam)
  return status === '进行中' && !exam.submitted_at
}

const getAvailableExams = () => {
  return exams.value.filter(exam => canTakeExam(exam))
}

const getCompletedExams = () => {
  return exams.value.filter(exam => exam.submitted_at)
}

const getUpcomingExams = () => {
  return exams.value.filter(exam => getExamStatus(exam) === '未开始')
}

const getExpiredExams = () => {
  return exams.value.filter(exam => getExamStatus(exam) === '已结束' && !exam.submitted_at)
}

const goBack = () => {
  router.back()
}
</script>

<template>
  <div class="student-exam">
    <!-- 头部导航 -->
    <van-nav-bar title="考试中心" left-arrow @click-left="goBack" />

    <!-- 标签页 -->
    <van-tabs v-model:active="activeTab">
      <van-tab title="可参加" name="available">
        <div class="content">
          <van-pull-refresh v-model="loading" @refresh="loadExams">
            <van-list>
              <van-card
                v-for="exam in getAvailableExams()"
                :key="exam.id"
                :title="exam.title"
                :desc="exam.description"
                class="exam-card available"
                @click="openDetailDialog(exam)"
              >
                <template #tags>
                  <van-tag type="success">可参加</van-tag>
                <van-tag type="primary" class="ml-1">{{ exam.max_score }}分</van-tag>
                </template>
                
                <template #footer>
                  <div class="exam-info">
                    <div class="exam-time">
                      <div>开始: {{ formatDate(exam.start_time) }}</div>
                      <div>结束: {{ formatDate(exam.end_time) }}</div>
                      <div>时长: {{ exam.duration }}分钟</div>
                    </div>
                    <div class="exam-actions">
                      <van-button 
                        type="success" 
                        @click.stop="openDetailDialog(exam)"
                      >
                        开始考试
                      </van-button>
                    </div>
                  </div>
                </template>
              </van-card>
            </van-list>
          </van-pull-refresh>

          <van-empty v-if="!loading && getAvailableExams().length === 0" description="暂无可参加的考试" />
        </div>
      </van-tab>
      
      <van-tab title="已完成" name="completed">
        <div class="content">
          <van-list>
            <van-card
              v-for="exam in getCompletedExams()"
              :key="exam.id"
              :title="exam.title"
              :desc="exam.description"
              class="exam-card completed"
              @click="openDetailDialog(exam)"
            >
              <template #tags>
                <van-tag type="success">已完成</van-tag>
                <van-tag v-if="exam.score !== null" type="primary" class="ml-1">
                  {{ exam.score }}/{{ exam.max_score }}分
                </van-tag>
                <van-tag v-else type="warning" class="ml-1">
                  待批改
                </van-tag>
              </template>
              
              <template #footer>
                <div class="exam-info">
                  <div class="submit-time">
                    提交时间: {{ formatDate(exam.submitted_at) }}
                  </div>
                </div>
              </template>
            </van-card>
          </van-list>
          
          <van-empty v-if="getCompletedExams().length === 0" description="暂无已完成的考试" />
        </div>
      </van-tab>
      
      <van-tab title="即将开始" name="upcoming">
        <div class="content">
          <van-list>
            <van-card
              v-for="exam in getUpcomingExams()"
              :key="exam.id"
              :title="exam.title"
              :desc="exam.description"
              class="exam-card upcoming"
            >
              <template #tags>
                <van-tag type="warning">即将开始</van-tag>
              </template>
              
              <template #footer>
                <div class="exam-info">
                  <div class="exam-time">
                    <div>开始: {{ formatDate(exam.start_time) }}</div>
                    <div>时长: {{ exam.duration }}分钟 | 总分: {{ exam.max_score }}分</div>
                  </div>
                </div>
              </template>
            </van-card>
          </van-list>
          
          <van-empty v-if="getUpcomingExams().length === 0" description="暂无即将开始的考试" />
        </div>
      </van-tab>
      
      <van-tab title="已过期" name="expired">
        <div class="content">
          <van-list>
            <van-card
              v-for="exam in getExpiredExams()"
              :key="exam.id"
              :title="exam.title"
              :desc="exam.description"
              class="exam-card expired"
            >
              <template #tags>
                <van-tag type="danger">已过期</van-tag>
              </template>
              
              <template #footer>
                <div class="exam-info">
                  <div class="exam-time">
                    结束时间: {{ formatDate(exam.end_time) }}
                  </div>
                </div>
              </template>
            </van-card>
          </van-list>
          
          <van-empty v-if="getExpiredExams().length === 0" description="暂无过期考试" />
        </div>
      </van-tab>
    </van-tabs>

    <!-- 考试详情弹窗 -->
    <van-dialog
      v-model:show="showDetailDialog"
      :title="currentExam.title"
      class="detail-dialog"
    >
      <div class="detail-content">
        <div class="exam-info-detail">
          <van-cell title="描述" :value="currentExam.description" />
          <van-cell title="开始时间" :value="formatDate(currentExam.start_time)" />
          <van-cell title="结束时间" :value="formatDate(currentExam.end_time)" />
          <van-cell title="考试时长" :value="currentExam.duration + '分钟'" />
          <van-cell title="总分" :value="currentExam.max_score + '分'" />
          <van-cell title="题目数量" :value="currentExam.question_ids?.length + '题'" />
          <van-cell v-if="currentExam.submitted_at" title="提交时间" :value="formatDate(currentExam.submitted_at)" />
          <van-cell v-if="currentExam.score !== null" title="得分" :value="currentExam.score + '/' + currentExam.max_score + '分'" />
        </div>
        
        <div v-if="canTakeExam(currentExam)" class="action-buttons">
          <van-button type="primary" block @click="startExam">
            开始考试
          </van-button>
        </div>
        
        <div v-else-if="currentExam.submitted_at" class="submitted-info">
          <van-notice-bar
            left-icon="info-o"
            :text="currentExam.score !== null ? '考试已完成，查看得分详情' : '考试已提交，等待批改'"
          />
        </div>
        
        <div v-else-if="getExamStatus(currentExam) === '未开始'" class="upcoming-info">
          <van-notice-bar
            left-icon="clock-o"
            text="考试尚未开始，请耐心等待"
            type="warning"
          />
        </div>
        
        <div v-else class="expired-info">
          <van-notice-bar
            left-icon="warning-o"
            text="考试已结束，无法参加"
            type="danger"
          />
        </div>
      </div>
    </van-dialog>

    <!-- 考试答题弹窗 -->
    <van-dialog
      v-model:show="showExamDialog"
      :title="'考试中 - ' + currentExam.title"
      class="exam-dialog"
      :show-cancel-button="false"
      :close-on-click-overlay="false"
    >
      <div class="exam-content">
        <!-- 考试头部信息 -->
        <div class="exam-header">
          <div class="timer">
            <van-icon name="clock-o" />
            <span class="time-text" :class="{ 'time-warning': timeLeft <= 300 }">
              剩余时间: {{ formatTime(timeLeft) }}
            </span>
          </div>
          <div class="progress">
            题目进度: {{ Object.keys(answers).filter(key => answers[key]).length }}/{{ questions.length }}
          </div>
        </div>
        
        <!-- 题目列表 -->
        <div class="questions-list">
          <div v-for="(question, index) in questions" :key="question.id" class="question-item">
            <div class="question-header">
              <span class="question-number">第{{ index + 1 }}题</span>
              <van-tag :type="question.difficulty === 'easy' ? 'success' : question.difficulty === 'medium' ? 'warning' : 'danger'">
                {{ question.difficulty === 'easy' ? '简单' : question.difficulty === 'medium' ? '中等' : '困难' }}
              </van-tag>
            </div>
            
            <div class="question-content">
              {{ question.content }}
            </div>
            
            <!-- 选择题 -->
            <div v-if="question.type === 'multiple_choice'" class="question-options">
              <van-radio-group v-model="answers[question.id]">
                <van-radio
                  v-for="(option, optionIndex) in question.options"
                  :key="optionIndex"
                  :name="String.fromCharCode(65 + optionIndex)"
                  class="option-item"
                >
                  {{ String.fromCharCode(65 + optionIndex) }}. {{ option }}
                </van-radio>
              </van-radio-group>
            </div>
            
            <!-- 填空题/简答题 -->
            <div v-else class="question-input">
              <van-field
                v-model="answers[question.id]"
                :type="question.type === 'short_answer' ? 'textarea' : 'text'"
                :rows="question.type === 'short_answer' ? 4 : 1"
                placeholder="请输入答案"
              />
            </div>
          </div>
        </div>
        
        <!-- 提交按钮 -->
        <div class="submit-actions">
          <van-button type="primary" block @click="submitExam">
            提交考试
          </van-button>
        </div>
      </div>
    </van-dialog>
  </div>
</template>

<style scoped>
.student-exam {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.content {
  padding: 16px;
}

.exam-card {
  margin-bottom: 16px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}

.exam-card.available {
  border-left: 4px solid #07c160;
}

.exam-card.completed {
  border-left: 4px solid #1989fa;
}

.exam-card.upcoming {
  border-left: 4px solid #ff976a;
}

.exam-card.expired {
  border-left: 4px solid #ee0a24;
  opacity: 0.7;
}

.exam-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.exam-time, .submit-time {
  font-size: 14px;
  color: #666;
  line-height: 1.4;
}

.exam-actions {
  display: flex;
  gap: 8px;
}

.detail-content {
  max-height: 70vh;
  overflow-y: auto;
}

.exam-info-detail {
  padding: 16px 0;
}

.action-buttons {
  padding: 16px;
}

.submitted-info, .upcoming-info, .expired-info {
  padding: 16px;
}

.exam-content {
  max-height: 90vh;
  overflow-y: auto;
  padding: 16px;
}

.exam-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 16px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.timer {
  display: flex;
  align-items: center;
  gap: 4px;
}

.time-text {
  font-weight: 600;
  color: #1989fa;
}

.time-text.time-warning {
  color: #ee0a24;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.5; }
}

.progress {
  font-size: 14px;
  color: #666;
}

.question-item {
  margin-bottom: 24px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.question-number {
  font-weight: 600;
  color: #1989fa;
}

.question-content {
  font-size: 16px;
  line-height: 1.5;
  margin-bottom: 16px;
  color: #333;
}

.question-options {
  margin-top: 12px;
}

.option-item {
  margin-bottom: 8px;
  padding: 8px 0;
}

.question-input {
  margin-top: 12px;
}

.submit-actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #eee;
  position: sticky;
  bottom: 0;
  background: #fff;
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
  width: 90vw;
}

:deep(.detail-dialog .van-dialog__content) {
  padding: 0;
}

:deep(.exam-dialog) {
  width: 95vw;
  max-width: 600px;
  height: 90vh;
}

:deep(.exam-dialog .van-dialog__content) {
  padding: 0;
  height: calc(90vh - 100px);
  overflow: hidden;
}

:deep(.van-radio) {
  width: 100%;
  margin: 0;
}

:deep(.van-radio__label) {
  width: 100%;
  padding: 8px 0;
}
</style>