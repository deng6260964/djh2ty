<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiService from '@/services/api'
import { showToast, showConfirmDialog } from 'vant'

const router = useRouter()
const homeworks = ref<any[]>([])
const loading = ref(false)
const showDetailDialog = ref(false)
const showSubmitDialog = ref(false)
const currentHomework = ref<any>({})
const questions = ref<any[]>([])
const answers = ref<Record<string, any>>({})
const activeTab = ref('pending')

onMounted(() => {
  loadHomeworks()
})

const loadHomeworks = async () => {
  try {
    loading.value = true
    const response = await apiService.getHomeworks()
    homeworks.value = response.data
  } catch (error) {
    showToast('加载作业失败')
  } finally {
    loading.value = false
  }
}

const openDetailDialog = async (homework: any) => {
  currentHomework.value = homework
  try {
    // 获取作业题目
    const questionPromises = homework.question_ids.map((id: string) => 
      apiService.getQuestion(parseInt(id))
    )
    const questionResponses = await Promise.all(questionPromises)
    questions.value = questionResponses.map(res => res.data)
    
    // 初始化答案
    answers.value = {}
    questions.value.forEach(q => {
      answers.value[q.id] = ''
    })
    
    showDetailDialog.value = true
  } catch (error) {
    showToast('加载作业详情失败')
  }
}

const openSubmitDialog = () => {
  showDetailDialog.value = false
  showSubmitDialog.value = true
}

const submitHomework = async () => {
  try {
    await showConfirmDialog({
      title: '确认提交',
      message: '确定要提交作业吗？提交后将无法修改。',
    })
    
    await apiService.submitHomework(currentHomework.value.id, {
      answers: answers.value
    })
    
    showToast('提交作业成功')
    showSubmitDialog.value = false
    loadHomeworks()
  } catch (error) {
    if (error !== 'cancel') {
      showToast('提交作业失败')
    }
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const getStatusText = (homework: any) => {
  const now = new Date()
  const dueDate = new Date(homework.due_date)
  
  if (homework.submitted_at) {
    return homework.score !== null ? '已批改' : '已提交'
  }
  
  if (now > dueDate) {
    return '已过期'
  }
  
  return '待提交'
}

const getStatusColor = (homework: any) => {
  const status = getStatusText(homework)
  if (status === '待提交') return 'warning'
  if (status === '已提交') return 'primary'
  if (status === '已批改') return 'success'
  if (status === '已过期') return 'danger'
  return 'default'
}

const isOverdue = (homework: any) => {
  const now = new Date()
  const dueDate = new Date(homework.due_date)
  return now > dueDate && !homework.submitted_at
}

const canSubmit = (homework: any) => {
  return !homework.submitted_at && !isOverdue(homework)
}

const getPendingHomeworks = () => {
  return homeworks.value.filter(h => !h.submitted_at && !isOverdue(h))
}

const getSubmittedHomeworks = () => {
  return homeworks.value.filter(h => h.submitted_at)
}

const getOverdueHomeworks = () => {
  return homeworks.value.filter(h => isOverdue(h))
}

const goBack = () => {
  router.back()
}
</script>

<template>
  <div class="student-homework">
    <!-- 头部导航 -->
    <van-nav-bar title="作业中心" left-arrow @click-left="goBack" />

    <!-- 标签页 -->
    <van-tabs v-model:active="activeTab">
      <van-tab title="待完成" name="pending">
        <div class="content">
          <van-pull-refresh v-model="loading" @refresh="loadHomeworks">
            <van-list>
              <van-card
                v-for="homework in getPendingHomeworks()"
                :key="homework.id"
                :title="homework.title"
                :desc="homework.description"
                class="homework-card"
                @click="openDetailDialog(homework)"
              >
                <template #tags>
                  <van-tag :type="getStatusColor(homework)">
                    {{ getStatusText(homework) }}
                  </van-tag>
                  <van-tag type="primary" class="ml-1">{{ homework.max_score }}分</van-tag>
                </template>
                
                <template #footer>
                  <div class="homework-info">
                    <div class="due-date">
                      截止时间: {{ formatDate(homework.due_date) }}
                    </div>
                    <div class="homework-actions">
                      <van-button 
                        type="success" 
                        @click.stop="openDetailDialog(homework)"
                      >
                        开始作答
                      </van-button>
                    </div>
                  </div>
                </template>
              </van-card>
            </van-list>
          </van-pull-refresh>

          <!-- 空状态 -->
          <van-empty v-if="!loading && getPendingHomeworks().length === 0" description="暂无待完成作业" />
        </div>
      </van-tab>
      
      <van-tab title="已提交" name="submitted">
        <div class="content">
          <van-list>
            <van-card
              v-for="homework in getSubmittedHomeworks()"
              :key="homework.id"
              :title="homework.title"
              :desc="homework.description"
              class="homework-card"
              @click="openDetailDialog(homework)"
            >
              <template #tags>
                <van-tag :type="getStatusColor(homework)">
                  {{ getStatusText(homework) }}
                </van-tag>
                <van-tag v-if="homework.score !== null" type="success" class="ml-1">
                  {{ homework.score }}/{{ homework.max_score }}分
                </van-tag>
              </template>
              
              <template #footer>
                <div class="homework-info">
                  <div class="submit-date">
                    提交时间: {{ formatDate(homework.submitted_at) }}
                  </div>
                </div>
              </template>
            </van-card>
          </van-list>
          
          <van-empty v-if="getSubmittedHomeworks().length === 0" description="暂无已提交作业" />
        </div>
      </van-tab>
      
      <van-tab title="已过期" name="overdue">
        <div class="content">
          <van-list>
            <van-card
              v-for="homework in getOverdueHomeworks()"
              :key="homework.id"
              :title="homework.title"
              :desc="homework.description"
              class="homework-card overdue"
            >
              <template #tags>
                <van-tag type="danger">已过期</van-tag>
              </template>
              
              <template #footer>
                <div class="homework-info">
                  <div class="due-date">
                    截止时间: {{ formatDate(homework.due_date) }}
                  </div>
                </div>
              </template>
            </van-card>
          </van-list>
          
          <van-empty v-if="getOverdueHomeworks().length === 0" description="暂无过期作业" />
        </div>
      </van-tab>
    </van-tabs>

    <!-- 作业详情弹窗 -->
    <van-dialog
      v-model:show="showDetailDialog"
      :title="currentHomework.title"
      class="detail-dialog"
    >
      <div class="detail-content">
        <div class="homework-info-detail">
          <van-cell title="描述" :value="currentHomework.description" />
          <van-cell title="总分" :value="currentHomework.max_score + '分'" />
          <van-cell title="截止时间" :value="formatDate(currentHomework.due_date)" />
          <van-cell v-if="currentHomework.submitted_at" title="提交时间" :value="formatDate(currentHomework.submitted_at)" />
          <van-cell v-if="currentHomework.score !== null" title="得分" :value="currentHomework.score + '/' + currentHomework.max_score + '分'" />
        </div>
        
        <div v-if="canSubmit(currentHomework)" class="action-buttons">
          <van-button type="primary" block @click="openSubmitDialog">
            开始答题
          </van-button>
        </div>
        
        <div v-else-if="currentHomework.submitted_at" class="submitted-info">
          <van-notice-bar
            left-icon="info-o"
            :text="currentHomework.score !== null ? '作业已批改，查看得分详情' : '作业已提交，等待批改'"
          />
        </div>
        
        <div v-else class="overdue-info">
          <van-notice-bar
            left-icon="warning-o"
            text="作业已过期，无法提交"
            type="warning"
          />
        </div>
      </div>
    </van-dialog>

    <!-- 答题弹窗 -->
    <van-dialog
      v-model:show="showSubmitDialog"
      :title="'答题 - ' + currentHomework.title"
      class="submit-dialog"
      :show-cancel-button="false"
    >
      <div class="submit-content">
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
        
        <div class="submit-actions">
          <van-button type="default" block @click="showSubmitDialog = false" class="mb-2">
            暂存草稿
          </van-button>
          <van-button type="primary" block @click="submitHomework">
            提交作业
          </van-button>
        </div>
      </div>
    </van-dialog>
  </div>
</template>

<style scoped>
.student-homework {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.content {
  padding: 16px;
}

.homework-card {
  margin-bottom: 16px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}

.homework-card.overdue {
  opacity: 0.7;
}

.homework-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.due-date, .submit-date {
  font-size: 14px;
  color: #666;
}

.homework-actions {
  display: flex;
  gap: 8px;
}

.detail-content {
  max-height: 70vh;
  overflow-y: auto;
}

.homework-info-detail {
  padding: 16px 0;
}

.action-buttons {
  padding: 16px;
}

.submitted-info, .overdue-info {
  padding: 16px;
}

.submit-content {
  max-height: 80vh;
  overflow-y: auto;
  padding: 16px;
}

.question-item {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
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
}

.ml-1 {
  margin-left: 4px;
}

.mb-2 {
  margin-bottom: 8px;
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

:deep(.submit-dialog) {
  width: 95vw;
  max-width: 500px;
}

:deep(.submit-dialog .van-dialog__content) {
  padding: 0;
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