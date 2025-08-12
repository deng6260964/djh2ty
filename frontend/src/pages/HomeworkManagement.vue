<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiService from '@/services/api'
import { showToast, showConfirmDialog } from 'vant'

const router = useRouter()
const homeworks = ref<any[]>([])
const courses = ref<any[]>([])
const questions = ref<any[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const currentHomework = ref<any>({})
const submissions = ref<any[]>([])

const formData = ref({
  title: '',
  description: '',
  course_id: '',
  question_ids: [],
  due_date: '',
  max_score: 100
})

const activeTab = ref('list')
const coursePickerRef = ref()
const datePickerRef = ref()
const questionPickerRef = ref()

onMounted(() => {
  loadHomeworks()
  loadCourses()
  loadQuestions()
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

const loadCourses = async () => {
  try {
    const response = await apiService.getCourses()
    courses.value = response.data
  } catch (error) {
    console.error('加载课程失败:', error)
  }
}

const loadQuestions = async () => {
  try {
    const response = await apiService.getQuestions()
    questions.value = response.data
  } catch (error) {
    console.error('加载题目失败:', error)
  }
}

const openCreateDialog = () => {
  formData.value = {
    title: '',
    description: '',
    course_id: '',
    question_ids: [],
    due_date: '',
    max_score: 100
  }
  showCreateDialog.value = true
}

const openDetailDialog = async (homework: any) => {
  currentHomework.value = homework
  try {
    const response = await apiService.getHomeworkSubmissions(homework.id)
    submissions.value = response.data
    showDetailDialog.value = true
  } catch (error) {
    showToast('加载作业详情失败')
  }
}

const createHomework = async () => {
  try {
    // 映射前端字段到后端期望的字段
    const data = {
      title: formData.value.title,
      description: formData.value.description,
      student_id: formData.value.course_id, // 临时使用course_id作为student_id，实际应该选择学生
      questions: formData.value.question_ids,
      due_date: formData.value.due_date,
      total_points: formData.value.max_score
    }
    await apiService.createHomework(data)
    showToast('创建作业成功')
    showCreateDialog.value = false
    loadHomeworks()
  } catch (error) {
    showToast('创建作业失败')
  }
}

const deleteHomework = async (homework: any) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: `确定要删除作业"${homework.title}"吗？`,
    })
    
    await apiService.deleteHomework(homework.id)
    showToast('删除作业成功')
    loadHomeworks()
  } catch (error) {
    if (error !== 'cancel') {
      showToast('删除作业失败')
    }
  }
}

const gradeSubmission = async (submission: any, score: number) => {
  try {
    await apiService.gradeHomework(submission.id, { score })
    showToast('评分成功')
    openDetailDialog(currentHomework.value) // 刷新提交列表
  } catch (error) {
    showToast('评分失败')
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '待提交',
    'submitted': '已提交',
    'graded': '已批改'
  }
  return statusMap[status] || status
}

const getStatusColor = (status: string) => {
  if (status === 'pending') return 'warning'
  if (status === 'submitted') return 'primary'
  if (status === 'graded') return 'success'
  return 'default'
}

const getCourseTitle = (courseId: string) => {
  const course = courses.value.find(c => c.id === courseId)
  return course ? course.name : '未知课程'
}

const goBack = () => {
  router.back()
}
</script>

<template>
  <div class="homework-management">
    <!-- 头部导航 -->
    <van-nav-bar title="作业管理" left-arrow @click-left="goBack">
      <template #right>
        <van-icon name="plus" @click="openCreateDialog" />
      </template>
    </van-nav-bar>

    <!-- 标签页 -->
    <van-tabs v-model:active="activeTab">
      <van-tab title="作业列表" name="list">
        <div class="content">
          <van-pull-refresh v-model="loading" @refresh="loadHomeworks">
            <van-list>
              <van-card
                v-for="homework in homeworks"
                :key="homework.id"
                :title="homework.title"
                :desc="homework.description"
                class="homework-card"
                @click="openDetailDialog(homework)"
              >
                <template #tags>
                  <van-tag type="primary">{{ getCourseTitle(homework.course_id) }}</van-tag>
                <van-tag type="warning" class="ml-1">{{ homework.max_score }}分</van-tag>
                </template>
                
                <template #footer>
                  <div class="homework-info">
                    <div class="due-date">
                      截止时间: {{ formatDate(homework.due_date) }}
                    </div>
                    <div class="homework-actions">
                      <van-button size="small" type="primary" @click.stop="openDetailDialog(homework)">
                        查看详情
                      </van-button>
                      <van-button size="small" type="danger" @click.stop="deleteHomework(homework)">
                        删除
                      </van-button>
                    </div>
                  </div>
                </template>
              </van-card>
            </van-list>
          </van-pull-refresh>

          <!-- 空状态 -->
          <van-empty v-if="!loading && homeworks.length === 0" description="暂无作业" />
        </div>
      </van-tab>
      
      <van-tab title="待批改" name="pending">
        <div class="content">
          <van-list>
            <van-card
              v-for="homework in homeworks.filter(h => h.submissions?.some((s: any) => s.status === 'submitted'))"
              :key="homework.id"
              :title="homework.title"
              class="homework-card"
              @click="openDetailDialog(homework)"
            >
              <template #tags>
                <van-tag type="danger">
                  {{ homework.submissions?.filter((s: any) => s.status === 'submitted').length || 0 }}份待批改
                </van-tag>
              </template>
            </van-card>
          </van-list>
        </div>
      </van-tab>
    </van-tabs>

    <!-- 创建作业弹窗 -->
    <van-dialog
      v-model:show="showCreateDialog"
      title="创建作业"
      show-cancel-button
      @confirm="createHomework"
      class="homework-dialog"
    >
      <van-form class="form">
        <van-field
          v-model="formData.title"
          label="作业标题"
          placeholder="请输入作业标题"
          required
        />
        <van-field
          v-model="formData.description"
          label="作业描述"
          placeholder="请输入作业描述"
          type="textarea"
          rows="3"
        />
        <van-field
          v-model="formData.course_id"
          label="所属课程"
          placeholder="请选择课程"
          readonly
          is-link
          @click="coursePickerRef.open()"
        />
        <van-field
          v-model="formData.due_date"
          label="截止时间"
          placeholder="请选择截止时间"
          readonly
          is-link
          @click="datePickerRef.open()"
        />
        <van-field
          v-model="formData.max_score"
          label="总分"
          placeholder="请输入总分"
          type="number"
          required
        />
        <van-field
          label="选择题目"
          placeholder="请选择题目"
          readonly
          is-link
          @click="questionPickerRef.open()"
        />
        <div v-if="formData.question_ids.length > 0" class="selected-questions">
          <van-tag
            v-for="questionId in formData.question_ids"
            :key="questionId"
            type="primary"

            closeable
            @close="formData.question_ids = formData.question_ids.filter(id => id !== questionId)"
            class="question-tag"
          >
            {{ questions.find(q => q.id === questionId)?.content?.substring(0, 20) }}...
          </van-tag>
        </div>
      </van-form>
      
      <!-- 选择器 -->
      <van-picker
        ref="coursePickerRef"
        :columns="courses.map(c => ({ text: c.name, value: c.id }))"
        @confirm="(value) => { formData.course_id = value.value; coursePickerRef.close() }"
      />
      <van-datetime-picker
        ref="datePickerRef"
        type="datetime"
        @confirm="(value) => { formData.due_date = value.toISOString(); datePickerRef.close() }"
      />
      <van-picker
        ref="questionPickerRef"
        :columns="questions.map(q => ({ text: q.content.substring(0, 30) + '...', value: q.id }))"
        @confirm="(value) => { 
          if (!formData.question_ids.includes(value.value)) {
            formData.question_ids.push(value.value)
          }
          questionPickerRef.close()
        }"
      />
    </van-dialog>

    <!-- 作业详情弹窗 -->
    <van-dialog
      v-model:show="showDetailDialog"
      :title="currentHomework.title"
      class="detail-dialog"
    >
      <div class="detail-content">
        <van-tabs>
          <van-tab title="作业信息">
            <div class="homework-info-detail">
              <van-cell title="课程" :value="getCourseTitle(currentHomework.course_id)" />
              <van-cell title="描述" :value="currentHomework.description" />
              <van-cell title="总分" :value="currentHomework.max_score + '分'" />
              <van-cell title="截止时间" :value="formatDate(currentHomework.due_date)" />
            </div>
          </van-tab>
          
          <van-tab title="提交情况">
            <div class="submissions-list">
              <van-card
                v-for="submission in submissions"
                :key="submission.id"
                :title="submission.student_name"
                class="submission-card"
              >
                <template #tags>
                  <van-tag :type="getStatusColor(submission.status)">
                    {{ getStatusText(submission.status) }}
                  </van-tag>
                  <van-tag v-if="submission.score !== null" type="success" class="ml-1">
                    {{ submission.score }}分
                  </van-tag>
                </template>
                
                <template #desc>
                  <div>提交时间: {{ formatDate(submission.submitted_at) }}</div>
                  <div v-if="submission.answers">答案: {{ JSON.stringify(submission.answers) }}</div>
                </template>
                
                <template #footer v-if="submission.status === 'submitted'">
                  <div class="grade-section">
                    <van-field
                      v-model="submission.tempScore"
                      label="评分"
                      type="number"
                      :placeholder="'满分' + currentHomework.max_score"
                      class="grade-input"
                    />
                    <van-button
                      size="small"
                      type="primary"
                      @click="gradeSubmission(submission, submission.tempScore)"
                    >
                      确认评分
                    </van-button>
                  </div>
                </template>
              </van-card>
              
              <van-empty v-if="submissions.length === 0" description="暂无提交" />
            </div>
          </van-tab>
        </van-tabs>
      </div>
    </van-dialog>
  </div>
</template>

<style scoped>
.homework-management {
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

.homework-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.due-date {
  font-size: 14px;
  color: #666;
}

.homework-actions {
  display: flex;
  gap: 8px;
}

.form {
  padding: 16px;
  max-height: 60vh;
  overflow-y: auto;
}

.selected-questions {
  margin-top: 8px;
}

.question-tag {
  margin: 4px 4px 4px 0;
}

.detail-content {
  max-height: 70vh;
  overflow-y: auto;
}

.homework-info-detail {
  padding: 16px 0;
}

.submissions-list {
  padding: 16px;
}

.submission-card {
  margin-bottom: 16px;
  border-radius: 8px;
  overflow: hidden;
}

.grade-section {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.grade-input {
  flex: 1;
}

.ml-1 {
  margin-left: 4px;
}

:deep(.van-nav-bar__right) {
  padding-right: 16px;
}

:deep(.van-card__content) {
  padding: 16px;
}

:deep(.van-card__footer) {
  padding: 0 16px 16px;
}

:deep(.homework-dialog .van-dialog__content) {
  max-height: 70vh;
  overflow: hidden;
}

:deep(.detail-dialog) {
  width: 90vw;
}

:deep(.detail-dialog .van-dialog__content) {
  padding: 0;
}
</style>