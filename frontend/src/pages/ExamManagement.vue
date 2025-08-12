<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiService from '@/services/api'
import { showToast, showConfirmDialog } from 'vant'

const router = useRouter()
const exams = ref<any[]>([])
const courses = ref<any[]>([])
const questions = ref<any[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const showEditDialog = ref(false)
const currentExam = ref<any>({})
const examSubmissions = ref<any[]>([])

const examForm = ref({
  title: '',
  description: '',
  course_id: [],
  start_time: '',
  end_time: '',
  duration: 60,
  max_score: 100,
  question_ids: []
})

const editForm = ref({
  title: '',
  description: '',
  start_time: '',
  end_time: '',
  duration: 60,
  max_score: 100
})

const selectedQuestions = ref<string[]>([])
const showQuestionPicker = ref(false)

onMounted(() => {
  loadExams()
  loadCourses()
  loadQuestions()
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

const loadCourses = async () => {
  try {
    const response = await apiService.getCourses()
    courses.value = response.data
  } catch (error) {
    showToast('加载课程失败')
  }
}

const loadQuestions = async () => {
  try {
    const response = await apiService.getQuestions()
    questions.value = response.data
  } catch (error) {
    showToast('加载题目失败')
  }
}

const openCreateDialog = () => {
  examForm.value = {
    title: '',
    description: '',
    course_id: [],
    start_time: '',
    end_time: '',
    duration: 60,
    max_score: 100,
    question_ids: []
  }
  selectedQuestions.value = []
  showCreateDialog.value = true
}

const openEditDialog = (exam: any) => {
  currentExam.value = exam
  editForm.value = {
    title: exam.title,
    description: exam.description,
    start_time: exam.start_time,
    end_time: exam.end_time,
    duration: exam.duration,
    max_score: exam.max_score
  }
  showEditDialog.value = true
}

const openDetailDialog = async (exam: any) => {
  currentExam.value = exam
  try {
    // 获取考试提交记录
    const response = await apiService.getExamSubmissions(exam.id)
    examSubmissions.value = response.data
    showDetailDialog.value = true
  } catch (error) {
    showToast('加载考试详情失败')
  }
}

const openQuestionPicker = () => {
  selectedQuestions.value = [...examForm.value.question_ids]
  showQuestionPicker.value = true
}

const confirmQuestionSelection = () => {
  examForm.value.question_ids = [...selectedQuestions.value]
  showQuestionPicker.value = false
}

const createExam = async () => {
  try {
    if (!examForm.value.title || !examForm.value.course_id || !examForm.value.start_time || !examForm.value.end_time) {
      showToast('请填写完整信息')
      return
    }
    
    if (examForm.value.question_ids.length === 0) {
      showToast('请选择考试题目')
      return
    }
    
    // 转换数据格式以匹配后端API
    const data = {
      title: examForm.value.title,
      description: examForm.value.description,
      student_id: examForm.value.course_id[0] || '', // 临时映射，实际应该是学生ID
      start_time: examForm.value.start_time.replace('T', ' ') + ':00',
      end_time: examForm.value.end_time.replace('T', ' ') + ':00',
      questions: examForm.value.question_ids,
      duration: examForm.value.duration,
      max_score: examForm.value.max_score
    }
    
    await apiService.createExam(data)
    showToast('创建考试成功')
    showCreateDialog.value = false
    loadExams()
  } catch (error) {
    showToast('创建考试失败')
  }
}

const updateExam = async () => {
  try {
    await apiService.updateExam(currentExam.value.id, editForm.value)
    showToast('更新考试成功')
    showEditDialog.value = false
    loadExams()
  } catch (error) {
    showToast('更新考试失败')
  }
}

const deleteExam = async (exam: any) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: `确定要删除考试"${exam.title}"吗？此操作不可恢复。`,
    })
    
    await apiService.deleteExam(exam.id)
    showToast('删除考试成功')
    loadExams()
  } catch (error) {
    if (error !== 'cancel') {
      showToast('删除考试失败')
    }
  }
}

const formatDateTime = (dateString: string) => {
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
  if (status === '未开始') return 'warning'
  if (status === '进行中') return 'success'
  if (status === '已结束') return 'default'
  return 'default'
}

const getCourseTitle = (courseId: string) => {
  const course = courses.value.find(c => c.id === courseId)
  return course ? course.title : '未知课程'
}

const getQuestionTitle = (questionId: string) => {
  const question = questions.value.find(q => q.id === questionId)
  return question ? question.content.substring(0, 30) + '...' : '未知题目'
}

const goBack = () => {
  router.back()
}
</script>

<template>
  <div class="exam-management">
    <!-- 头部导航 -->
    <van-nav-bar title="考试管理" left-arrow @click-left="goBack">
      <template #right>
        <van-button type="primary" size="small" @click="openCreateDialog">
          创建考试
        </van-button>
      </template>
    </van-nav-bar>

    <!-- 考试列表 -->
    <div class="content">
      <van-pull-refresh v-model="loading" @refresh="loadExams">
        <van-list>
          <van-card
            v-for="exam in exams"
            :key="exam.id"
            :title="exam.title"
            :desc="exam.description"
            class="exam-card"
            @click="openDetailDialog(exam)"
          >
            <template #tags>
              <van-tag :type="getStatusColor(exam)">
                {{ getExamStatus(exam) }}
              </van-tag>
              <van-tag type="primary" class="ml-1">
                {{ getCourseTitle(exam.course_id) }}
              </van-tag>
            </template>
            
            <template #footer>
              <div class="exam-info">
                <div class="exam-time">
                  <div>开始: {{ formatDateTime(exam.start_time) }}</div>
                  <div>结束: {{ formatDateTime(exam.end_time) }}</div>
                  <div>时长: {{ exam.duration }}分钟 | 总分: {{ exam.max_score }}分</div>
                </div>
                <div class="exam-actions">
                  <van-button size="small" @click.stop="openEditDialog(exam)">
                    编辑
                  </van-button>
                  <van-button size="small" type="danger" @click.stop="deleteExam(exam)">
                    删除
                  </van-button>
                </div>
              </div>
            </template>
          </van-card>
        </van-list>
      </van-pull-refresh>

      <!-- 空状态 -->
      <van-empty v-if="!loading && exams.length === 0" description="暂无考试" />
    </div>

    <!-- 创建考试弹窗 -->
    <van-dialog
      v-model:show="showCreateDialog"
      title="创建考试"
      show-cancel-button
      @confirm="createExam"
      class="create-dialog"
    >
      <div class="form-content">
        <van-form>
          <van-field
            v-model="examForm.title"
            label="考试标题"
            placeholder="请输入考试标题"
            required
          />
          
          <van-field
            v-model="examForm.description"
            label="考试描述"
            type="textarea"
            placeholder="请输入考试描述"
            rows="3"
          />
          
          <van-field label="所属课程" required>
            <template #input>
              <van-picker
                v-model="examForm.course_id"
                :columns="[courses.map(c => ({ text: c.title, value: c.id }))]"
                placeholder="请选择课程"
              />
            </template>
          </van-field>
          
          <van-field
            v-model="examForm.start_time"
            label="开始时间"
            type="datetime-local"
            required
          />
          
          <van-field
            v-model="examForm.end_time"
            label="结束时间"
            type="datetime-local"
            required
          />
          
          <van-field
            v-model="examForm.duration"
            label="考试时长"
            type="number"
            placeholder="分钟"
            required
          />
          
          <van-field
            v-model="examForm.max_score"
            label="总分"
            type="number"
            required
          />
          
          <van-field label="考试题目" required>
            <template #input>
              <van-button type="primary" size="small" @click="openQuestionPicker">
                选择题目 ({{ examForm.question_ids.length }})
              </van-button>
            </template>
          </van-field>
        </van-form>
      </div>
    </van-dialog>

    <!-- 编辑考试弹窗 -->
    <van-dialog
      v-model:show="showEditDialog"
      title="编辑考试"
      show-cancel-button
      @confirm="updateExam"
      class="edit-dialog"
    >
      <div class="form-content">
        <van-form>
          <van-field
            v-model="editForm.title"
            label="考试标题"
            placeholder="请输入考试标题"
            required
          />
          
          <van-field
            v-model="editForm.description"
            label="考试描述"
            type="textarea"
            placeholder="请输入考试描述"
            rows="3"
          />
          
          <van-field
            v-model="editForm.start_time"
            label="开始时间"
            type="datetime-local"
            required
          />
          
          <van-field
            v-model="editForm.end_time"
            label="结束时间"
            type="datetime-local"
            required
          />
          
          <van-field
            v-model="editForm.duration"
            label="考试时长"
            type="number"
            placeholder="分钟"
            required
          />
          
          <van-field
            v-model="editForm.max_score"
            label="总分"
            type="number"
            required
          />
        </van-form>
      </div>
    </van-dialog>

    <!-- 考试详情弹窗 -->
    <van-dialog
      v-model:show="showDetailDialog"
      :title="currentExam.title"
      class="detail-dialog"
    >
      <div class="detail-content">
        <van-tabs>
          <van-tab title="考试信息">
            <div class="exam-info-detail">
              <van-cell title="描述" :value="currentExam.description" />
              <van-cell title="所属课程" :value="getCourseTitle(currentExam.course_id)" />
              <van-cell title="开始时间" :value="formatDateTime(currentExam.start_time)" />
              <van-cell title="结束时间" :value="formatDateTime(currentExam.end_time)" />
              <van-cell title="考试时长" :value="currentExam.duration + '分钟'" />
              <van-cell title="总分" :value="currentExam.max_score + '分'" />
              <van-cell title="状态">
                <template #value>
                  <van-tag :type="getStatusColor(currentExam)">
                    {{ getExamStatus(currentExam) }}
                  </van-tag>
                </template>
              </van-cell>
            </div>
          </van-tab>
          
          <van-tab title="题目列表">
            <div class="questions-list">
              <van-cell
                v-for="(questionId, index) in currentExam.question_ids"
                :key="questionId"
                :title="`第${index + 1}题`"
                :value="getQuestionTitle(questionId)"
              />
            </div>
          </van-tab>
          
          <van-tab title="提交记录">
            <div class="submissions-list">
              <van-card
                v-for="submission in examSubmissions"
                :key="submission.id"
                :title="submission.student_name"
                class="submission-card"
              >
                <template #desc>
                  <div>提交时间: {{ formatDateTime(submission.submitted_at) }}</div>
                  <div v-if="submission.score !== null">得分: {{ submission.score }}/{{ currentExam.max_score }}</div>
                  <div v-else>待批改</div>
                </template>
                
                <template #tags>
                  <van-tag :type="submission.score !== null ? 'success' : 'warning'">
                    {{ submission.score !== null ? '已批改' : '待批改' }}
                  </van-tag>
                </template>
              </van-card>
              
              <van-empty v-if="examSubmissions.length === 0" description="暂无提交记录" />
            </div>
          </van-tab>
        </van-tabs>
      </div>
    </van-dialog>

    <!-- 题目选择弹窗 -->
    <van-dialog
      v-model:show="showQuestionPicker"
      title="选择题目"
      show-cancel-button
      @confirm="confirmQuestionSelection"
      class="question-picker-dialog"
    >
      <div class="question-picker-content">
        <van-checkbox-group v-model="selectedQuestions">
          <van-cell
            v-for="question in questions"
            :key="question.id"
            clickable
            @click="() => {
              const index = selectedQuestions.indexOf(question.id)
              if (index > -1) {
                selectedQuestions.splice(index, 1)
              } else {
                selectedQuestions.push(question.id)
              }
            }"
          >
            <template #title>
              <van-checkbox :name="question.id" />
              <span class="ml-2">{{ question.content.substring(0, 50) }}...</span>
            </template>
            
            <template #label>
              <van-tag :type="question.difficulty === 'easy' ? 'success' : question.difficulty === 'medium' ? 'warning' : 'danger'">
                {{ question.difficulty === 'easy' ? '简单' : question.difficulty === 'medium' ? '中等' : '困难' }}
              </van-tag>
              <van-tag type="primary" class="ml-1">
                {{ question.type === 'multiple_choice' ? '选择题' : question.type === 'fill_blank' ? '填空题' : '简答题' }}
              </van-tag>
            </template>
          </van-cell>
        </van-checkbox-group>
      </div>
    </van-dialog>
  </div>
</template>

<style scoped>
.exam-management {
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

.exam-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.exam-time {
  font-size: 14px;
  color: #666;
  line-height: 1.4;
}

.exam-actions {
  display: flex;
  gap: 8px;
}

.form-content {
  max-height: 60vh;
  overflow-y: auto;
  padding: 16px;
}

.detail-content {
  max-height: 70vh;
  overflow-y: auto;
}

.exam-info-detail {
  padding: 16px 0;
}

.questions-list, .submissions-list {
  padding: 16px;
}

.submission-card {
  margin-bottom: 12px;
}

.question-picker-content {
  max-height: 60vh;
  overflow-y: auto;
  padding: 16px;
}

.ml-1 {
  margin-left: 4px;
}

.ml-2 {
  margin-left: 8px;
}

:deep(.van-card__content) {
  padding: 16px;
}

:deep(.van-card__footer) {
  padding: 0 16px 16px;
}

:deep(.create-dialog), :deep(.edit-dialog) {
  width: 90vw;
}

:deep(.detail-dialog) {
  width: 95vw;
  max-width: 600px;
}

:deep(.question-picker-dialog) {
  width: 90vw;
  max-width: 500px;
}

:deep(.van-dialog__content) {
  padding: 0;
}

:deep(.van-checkbox) {
  margin-right: 8px;
}
</style>