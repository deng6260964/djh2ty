<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiService from '@/services/api'
import { showToast, showConfirmDialog } from 'vant'

const router = useRouter()
const courses = ref<any[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const currentCourse = ref<any>({})

const formData = ref({
  name: '',
  description: '',
  grade: '',
  subject: 'English'
})

onMounted(() => {
  loadCourses()
})

const loadCourses = async () => {
  try {
    loading.value = true
    const response = await apiService.getCourseManagement()
    if (response.success) {
      courses.value = response.data || []
    } else {
      showToast(response.message || '获取课程列表失败')
    }
  } catch (error) {
    console.error('获取课程列表失败:', error)
    showToast('获取课程列表失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  formData.value = {
    name: '',
    description: '',
    grade: '',
    subject: 'English'
  }
  showCreateDialog.value = true
}

const openEditDialog = (course: any) => {
  currentCourse.value = course
  formData.value = {
    name: course.name,
    description: course.description,
    grade: course.grade,
    subject: course.subject
  }
  showEditDialog.value = true
}

const createCourse = async () => {
  try {
    await apiService.createCourse(formData.value)
    showToast('创建课程成功')
    showCreateDialog.value = false
    loadCourses()
  } catch (error) {
    showToast('创建课程失败')
  }
}

const updateCourse = async () => {
  try {
    await apiService.updateCourse(currentCourse.value.id, formData.value)
    showToast('更新课程成功')
    showEditDialog.value = false
    loadCourses()
  } catch (error) {
    showToast('更新课程失败')
  }
}

const deleteCourse = async (course: any) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: `确定要删除课程"${course.name}"吗？`,
    })
    
    await apiService.deleteCourse(course.id)
    showToast('删除课程成功')
    loadCourses()
  } catch (error) {
    if (error !== 'cancel') {
      showToast('删除课程失败')
    }
  }
}

const goBack = () => {
  router.back()
}
</script>

<template>
  <div class="course-management">
    <!-- 头部导航 -->
    <van-nav-bar title="课程管理" left-arrow @click-left="goBack">
      <template #right>
        <van-icon name="plus" @click="openCreateDialog" />
      </template>
    </van-nav-bar>

    <!-- 课程列表 -->
    <div class="content">
      <van-pull-refresh v-model="loading" @refresh="loadCourses">
        <van-list>
          <van-card
            v-for="course in courses"
            :key="course.id"
            :title="course.name"
            :desc="course.description"
            :tag="course.grade"
            class="course-card"
          >
            <template #footer>
              <div class="course-actions">
                <van-button size="small" type="primary" @click="openEditDialog(course)">
                  编辑
                </van-button>
                <van-button size="small" type="danger" @click="deleteCourse(course)">
                  删除
                </van-button>
              </div>
            </template>
          </van-card>
        </van-list>
      </van-pull-refresh>

      <!-- 空状态 -->
      <van-empty v-if="!loading && courses.length === 0" description="暂无课程" />
    </div>

    <!-- 创建课程弹窗 -->
    <van-dialog
      v-model:show="showCreateDialog"
      title="创建课程"
      show-cancel-button
      @confirm="createCourse"
    >
      <van-form class="form">
        <van-field
          v-model="formData.name"
          label="课程名称"
          placeholder="请输入课程名称"
          required
        />
        <van-field
          v-model="formData.description"
          label="课程描述"
          placeholder="请输入课程描述"
          type="textarea"
          rows="3"
        />
        <van-field
          v-model="formData.grade"
          label="年级"
          placeholder="请输入年级"
          required
        />
        <van-field
          v-model="formData.subject"
          label="科目"
          placeholder="请输入科目"
          required
        />
      </van-form>
    </van-dialog>

    <!-- 编辑课程弹窗 -->
    <van-dialog
      v-model:show="showEditDialog"
      title="编辑课程"
      show-cancel-button
      @confirm="updateCourse"
    >
      <van-form class="form">
        <van-field
          v-model="formData.name"
          label="课程名称"
          placeholder="请输入课程名称"
          required
        />
        <van-field
          v-model="formData.description"
          label="课程描述"
          placeholder="请输入课程描述"
          type="textarea"
          rows="3"
        />
        <van-field
          v-model="formData.grade"
          label="年级"
          placeholder="请输入年级"
          required
        />
        <van-field
          v-model="formData.subject"
          label="科目"
          placeholder="请输入科目"
          required
        />
      </van-form>
    </van-dialog>
  </div>
</template>

<style scoped>
.course-management {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.content {
  padding: 16px;
}

.course-card {
  margin-bottom: 16px;
  border-radius: 8px;
  overflow: hidden;
}

.course-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.form {
  padding: 16px;
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
</style>