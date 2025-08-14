<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiService from '@/services/api'
import { showToast, showConfirmDialog } from 'vant'

const router = useRouter()
const questions = ref<any[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showGenerateDialog = ref(false)
const currentQuestion = ref<any>({})

// Picker refs
const typePickerRef = ref(null)
const difficultyPickerRef = ref(null)
const editTypePickerRef = ref(null)
const editDifficultyPickerRef = ref(null)
const generateDifficultyPickerRef = ref(null)

// Picker show states
const showTypePicker = ref(false)
const showDifficultyPicker = ref(false)
const showEditTypePicker = ref(false)
const showEditDifficultyPicker = ref(false)
const showGenerateDifficultyPicker = ref(false)

const formData = ref({
  content: '',
  type: 'multiple_choice',
  options: ['', '', '', ''],
  correct_answer: '',
  difficulty: 'medium',
  category: '',
  explanation: ''
})

const generateData = ref({
  topic: '',
  difficulty: 'medium',
  count: 5
})

const questionTypes = [
  { text: '单选题', value: 'single_choice' },
  { text: '多选题', value: 'multiple_choice' },
  { text: '填空题', value: 'fill_blank' },
  { text: '简答题', value: 'short_answer' }
]

const difficulties = [
  { text: '简单', value: 'easy' },
  { text: '中等', value: 'medium' },
  { text: '困难', value: 'hard' }
]

onMounted(() => {
  loadQuestions()
})

const loadQuestions = async () => {
  try {
    loading.value = true
    const response = await apiService.getQuestions()
    questions.value = response.data
  } catch (error) {
    showToast('加载题目失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  formData.value = {
    content: '',
    type: 'single_choice',
    options: ['', '', '', ''],
    correct_answer: '',
    difficulty: 'medium',
    category: '',
    explanation: ''
  }
  console.log('openCreateDialog - formData initialized:', formData.value)
  console.log('getTypeText result:', getTypeText(formData.value.type))
  console.log('getDifficultyText result:', getDifficultyText(formData.value.difficulty))
  showCreateDialog.value = true
}

const openEditDialog = (question: any) => {
  currentQuestion.value = question
  formData.value = {
    content: question.title || question.content, // 优先使用title字段
    type: question.question_type || question.type,
    options: Array.isArray(question.options) ? question.options : ['', '', '', ''],
    correct_answer: question.correct_answer || '',
    difficulty: question.difficulty || 'medium',
    category: question.category || '',
    explanation: question.explanation || ''
  }
  showEditDialog.value = true
}

const openGenerateDialog = () => {
  generateData.value = {
    topic: '',
    difficulty: 'medium',
    count: 5
  }
  showGenerateDialog.value = true
}

const createQuestion = async () => {
  try {
    const data: any = { ...formData.value }
    // 将content字段映射为title字段
    data.title = data.content
    data.points = 10 // 设置默认分值
    if (data.type !== 'single_choice') {
      delete data.options
    }
    await apiService.createQuestion(data)
    showToast('创建题目成功')
    showCreateDialog.value = false
    loadQuestions()
  } catch (error) {
    showToast('创建题目失败')
  }
}

const updateQuestion = async () => {
  try {
    const data: any = { ...formData.value }
    // 将content字段映射为title字段
    data.title = data.content
    if (data.type !== 'single_choice') {
      delete data.options
    }
    await apiService.updateQuestion(currentQuestion.value.id, data)
    showToast('更新题目成功')
    showEditDialog.value = false
    loadQuestions()
  } catch (error) {
    showToast('更新题目失败')
  }
}

const generateQuestions = async () => {
  try {
    await apiService.autoGenerateQuestions(generateData.value)
    showToast('生成题目成功')
    showGenerateDialog.value = false
    loadQuestions()
  } catch (error) {
    showToast('生成题目失败')
  }
}

const deleteQuestion = async (question: any) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: '确定要删除这道题目吗？',
    })
    
    // 调试信息：检查题目ID
    console.log('删除题目，题目数据:', question)
    console.log('题目ID:', question.id)
    
    if (!question.id) {
      showToast('题目ID不存在，无法删除')
      return
    }
    
    await apiService.deleteQuestion(question.id)
    showToast('删除题目成功')
    loadQuestions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除题目失败:', error)
      showToast('删除题目失败')
    }
  }
}

const getDifficultyText = (difficulty: string) => {
  const item = difficulties.find(d => d.value === difficulty)
  return item ? item.text : difficulty
}

const getTypeText = (type: string) => {
  const item = questionTypes.find(t => t.value === type)
  return item ? item.text : type
}

const onTypeConfirm = (value: any) => {
  console.log('onTypeConfirm called with:', value)
  console.log('formData before update:', formData.value)
  formData.value.type = value.selectedOptions[0].value
  console.log('formData after update:', formData.value)
  console.log('getTypeText result:', getTypeText(formData.value.type))
  showTypePicker.value = false
}

const onDifficultyConfirm = (value: any) => {
  console.log('onDifficultyConfirm called with:', value)
  console.log('formData before update:', formData.value)
  formData.value.difficulty = value.selectedOptions[0].value
  console.log('formData after update:', formData.value)
  console.log('getDifficultyText result:', getDifficultyText(formData.value.difficulty))
  showDifficultyPicker.value = false
}

const onEditTypeConfirm = (value: any) => {
  formData.value.type = value.selectedOptions[0].value
  showEditTypePicker.value = false
}

const onEditDifficultyConfirm = (value: any) => {
  formData.value.difficulty = value.selectedOptions[0].value
  showEditDifficultyPicker.value = false
}

const goBack = () => {
  router.back()
}
</script>

<template>
  <div class="question-management">
    <!-- 头部导航 -->
    <van-nav-bar title="题目管理" left-arrow @click-left="goBack">
      <template #right>
        <van-icon name="plus" @click="openCreateDialog" class="mr-3" />
        <van-icon name="bulb-o" @click="openGenerateDialog" />
      </template>
    </van-nav-bar>

    <!-- 题目列表 -->
    <div class="content">
      <van-pull-refresh v-model="loading" @refresh="loadQuestions">
        <van-list>
          <van-card
            v-for="question in questions"
            :key="question.id"
            :title="question.title || question.content"
            class="question-card"
          >
            <template #tags>
              <van-tag type="primary">{{ getTypeText(question.question_type || question.type) }}</van-tag>
              <van-tag 
                :type="question.difficulty === 'easy' ? 'success' : question.difficulty === 'medium' ? 'warning' : 'danger'"

                class="ml-1"
              >
                {{ getDifficultyText(question.difficulty) }}
              </van-tag>
              <van-tag v-if="question.category" type="default" class="ml-1">
                {{ question.category }}
              </van-tag>
            </template>
            
            <template #desc>
              <div v-if="(question.question_type || question.type) === 'single_choice' && question.options">
                <div v-for="(option, index) in question.options" :key="index" class="option">
                  {{ String.fromCharCode(65 + index) }}. {{ option }}
                </div>
                <div class="correct-answer">
                  正确答案: {{ question.correct_answer }}
                </div>
              </div>
              <div v-else class="correct-answer">
                参考答案: {{ question.correct_answer }}
              </div>
            </template>
            
            <template #footer>
              <div class="question-actions">
                <van-button size="small" type="primary" @click="openEditDialog(question)">
                  编辑
                </van-button>
                <van-button size="small" type="danger" @click="deleteQuestion(question)">
                  删除
                </van-button>
              </div>
            </template>
          </van-card>
        </van-list>
      </van-pull-refresh>

      <!-- 空状态 -->
      <van-empty v-if="!loading && questions.length === 0" description="暂无题目" />
    </div>

    <!-- 创建题目弹窗 -->
    <van-dialog
      v-model:show="showCreateDialog"
      title="创建题目"
      show-cancel-button
      @confirm="createQuestion"
      class="question-dialog"
    >
      <van-form class="form">
        <van-field
          v-model="formData.content"
          label="题目内容"
          placeholder="请输入题目内容"
          type="textarea"
          rows="3"
          required
        />
        <van-field
          :model-value="getTypeText(formData.type)"
          label="题目类型"
          placeholder="请选择题目类型"
          readonly
          is-link
          @click="showTypePicker = true"
        />
        <van-field
          :model-value="getDifficultyText(formData.difficulty)"
          label="难度"
          placeholder="请选择难度"
          readonly
          is-link
          @click="showDifficultyPicker = true"
        />
        <van-field
          v-model="formData.category"
          label="分类"
          placeholder="请输入分类"
        />
        
        <!-- 选择题选项 -->
        <template v-if="formData.type === 'single_choice'">
          <van-field
            v-for="(option, index) in formData.options"
            :key="index"
            v-model="formData.options[index]"
            :label="`选项${String.fromCharCode(65 + index)}`"
            :placeholder="`请输入选项${String.fromCharCode(65 + index)}`"
          />
        </template>
        
        <van-field
          v-model="formData.correct_answer"
          label="正确答案"
          placeholder="请输入正确答案"
          required
        />
        <van-field
          v-model="formData.explanation"
          label="解析"
          placeholder="请输入解析（可选）"
          type="textarea"
          rows="2"
        />
      </van-form>
      
      <!-- 选择器弹窗 -->
      <van-popup v-model:show="showTypePicker" position="bottom">
        <van-picker
          :columns="questionTypes"
          :default-index="questionTypes.findIndex(item => item.value === formData.type)"
          @confirm="onTypeConfirm"
          @cancel="showTypePicker = false"
        />
      </van-popup>
      <van-popup v-model:show="showDifficultyPicker" position="bottom">
        <van-picker
          :columns="difficulties"
          :default-index="difficulties.findIndex(item => item.value === formData.difficulty)"
          @confirm="onDifficultyConfirm"
          @cancel="showDifficultyPicker = false"
        />
      </van-popup>
    </van-dialog>

    <!-- 编辑题目弹窗 -->
    <van-dialog
      v-model:show="showEditDialog"
      title="编辑题目"
      show-cancel-button
      @confirm="updateQuestion"
      class="question-dialog"
    >
      <van-form class="form">
        <van-field
          v-model="formData.content"
          label="题目内容"
          placeholder="请输入题目内容"
          type="textarea"
          rows="3"
          required
        />
        <van-field
          :model-value="getTypeText(formData.type)"
          label="题目类型"
          placeholder="请选择题目类型"
          readonly
          is-link
          @click="showEditTypePicker = true"
        />
        <van-field
          :model-value="getDifficultyText(formData.difficulty)"
          label="难度"
          placeholder="请选择难度"
          readonly
          is-link
          @click="showEditDifficultyPicker = true"
        />
        <van-field
          v-model="formData.category"
          label="分类"
          placeholder="请输入分类"
        />
        
        <!-- 选择题选项 -->
        <template v-if="formData.type === 'single_choice'">
          <van-field
            v-for="(option, index) in formData.options"
            :key="index"
            v-model="formData.options[index]"
            :label="`选项${String.fromCharCode(65 + index)}`"
            :placeholder="`请输入选项${String.fromCharCode(65 + index)}`"
          />
        </template>
        
        <van-field
          v-model="formData.correct_answer"
          label="正确答案"
          placeholder="请输入正确答案"
          required
        />
        <van-field
          v-model="formData.explanation"
          label="解析"
          placeholder="请输入解析（可选）"
          type="textarea"
          rows="2"
        />
      </van-form>
      
      <!-- 选择器弹窗 -->
      <van-popup v-model:show="showEditTypePicker" position="bottom">
        <van-picker
          :columns="questionTypes"
          :default-index="questionTypes.findIndex(item => item.value === formData.type)"
          @confirm="onEditTypeConfirm"
          @cancel="showEditTypePicker = false"
        />
      </van-popup>
      <van-popup v-model:show="showEditDifficultyPicker" position="bottom">
        <van-picker
          :columns="difficulties"
          :default-index="difficulties.findIndex(item => item.value === formData.difficulty)"
          @confirm="onEditDifficultyConfirm"
          @cancel="showEditDifficultyPicker = false"
        />
      </van-popup>
    </van-dialog>

    <!-- 自动生成题目弹窗 -->
    <van-dialog
      v-model:show="showGenerateDialog"
      title="自动生成题目"
      show-cancel-button
      @confirm="generateQuestions"
    >
      <van-form class="form">
        <van-field
          v-model="generateData.topic"
          label="主题"
          placeholder="请输入题目主题"
          required
        />
        <van-field
          :model-value="getDifficultyText(generateData.difficulty)"
          label="难度"
          placeholder="请选择难度"
          readonly
          is-link
          @click="showGenerateDifficultyPicker = true"
        />
        <van-field
          v-model="generateData.count"
          label="数量"
          placeholder="请输入生成数量"
          type="number"
          required
        />
      </van-form>
      
      <!-- 选择器弹窗 -->
      <van-popup v-model:show="showGenerateDifficultyPicker" position="bottom">
        <van-picker
          :columns="difficulties"
          :default-index="difficulties.findIndex(item => item.value === generateData.difficulty)"
          @confirm="(value) => { generateData.difficulty = value.value; showGenerateDifficultyPicker = false }"
          @cancel="showGenerateDifficultyPicker = false"
        />
      </van-popup>
    </van-dialog>
  </div>
</template>

<style scoped>
.question-management {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.content {
  padding: 16px;
}

.question-card {
  margin-bottom: 16px;
  border-radius: 8px;
  overflow: hidden;
}

.option {
  margin: 4px 0;
  font-size: 14px;
  color: #666;
}

.correct-answer {
  margin-top: 8px;
  font-size: 14px;
  color: #1989fa;
  font-weight: 500;
}

.question-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.form {
  padding: 16px;
  max-height: 60vh;
  overflow-y: auto;
}

.mr-3 {
  margin-right: 12px;
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

:deep(.question-dialog .van-dialog__content) {
  max-height: 70vh;
  overflow: hidden;
}
</style>