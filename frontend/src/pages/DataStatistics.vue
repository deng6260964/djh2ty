<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiService from '@/services/api'
import { showToast } from 'vant'

const router = useRouter()
const loading = ref(false)
const statistics = ref<any>({})
const activeTab = ref('overview')
const dateRange = ref<string[]>([])
const showDatePicker = ref(false)

// 日期范围选项
const dateRangeOptions = [
  { text: '最近7天', value: 7 },
  { text: '最近30天', value: 30 },
  { text: '最近90天', value: 90 },
  { text: '自定义', value: 'custom' }
]
const selectedDateRange = ref<number | string>(30)

onMounted(() => {
  loadStatistics()
})

const loadStatistics = async () => {
  try {
    loading.value = true
    const response = await apiService.getTeachingStatistics()
    statistics.value = response.data
  } catch (error) {
    showToast('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

const onDateRangeChange = (value: number | string) => {
  selectedDateRange.value = typeof value === 'string' ? value : Number(value)
  if (value === 'custom') {
    showDatePicker.value = true
  } else {
    // 重新加载指定天数的数据
    loadStatistics()
  }
}

const onDateConfirm = (values: string[]) => {
  dateRange.value = values
  showDatePicker.value = false
  // 重新加载自定义日期范围的数据
  loadStatistics()
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const getScoreColor = (score: number) => {
  if (score >= 90) return '#52c41a'
  if (score >= 80) return '#1890ff'
  if (score >= 60) return '#faad14'
  return '#ff4d4f'
}

const getGrowthIcon = (growth: number) => {
  if (growth > 0) return 'arrow-up'
  if (growth < 0) return 'arrow-down'
  return 'minus'
}

const getGrowthColor = (growth: number) => {
  if (growth > 0) return '#52c41a'
  if (growth < 0) return '#ff4d4f'
  return '#666'
}

const goBack = () => {
  router.back()
}
</script>

<template>
  <div class="data-statistics">
    <!-- 头部导航 -->
    <van-nav-bar title="数据统计" left-arrow @click-left="goBack" />

    <!-- 日期范围选择 -->
    <div class="date-filter">
      <van-cell-group>
        <van-field
          readonly
          clickable
          label="统计周期"
          :value="selectedDateRange === 'custom' ? '自定义' : `最近${selectedDateRange}天`"
          @click="showDatePicker = true"
        />
      </van-cell-group>
    </div>

    <!-- 标签页 -->
    <van-tabs v-model:active="activeTab">
      <van-tab title="总览" name="overview">
        <div class="content">
          <!-- 核心指标 -->
          <div class="overview-cards">
            <van-grid :column-num="2" :border="false">
              <van-grid-item>
                <div class="metric-card">
                  <div class="metric-icon">
                    <van-icon name="friends-o" color="#1989fa" :size="24" />
                  </div>
                  <div class="metric-info">
                    <div class="metric-number">{{ statistics.total_students || 0 }}</div>
                    <div class="metric-label">学生总数</div>
                    <div class="metric-growth" :style="{ color: getGrowthColor(statistics.student_growth || 0) }">
                      <van-icon :name="getGrowthIcon(statistics.student_growth || 0)" :size="12" />
                      {{ Math.abs(statistics.student_growth || 0) }}%
                    </div>
                  </div>
                </div>
              </van-grid-item>
              
              <van-grid-item>
                <div class="metric-card">
                  <div class="metric-icon">
                    <van-icon name="bookmark-o" color="#52c41a" :size="24" />
                  </div>
                  <div class="metric-info">
                    <div class="metric-number">{{ statistics.total_courses || 0 }}</div>
                    <div class="metric-label">课程数量</div>
                    <div class="metric-growth" :style="{ color: getGrowthColor(statistics.course_growth || 0) }">
                      <van-icon :name="getGrowthIcon(statistics.course_growth || 0)" :size="12" />
                      {{ Math.abs(statistics.course_growth || 0) }}%
                    </div>
                  </div>
                </div>
              </van-grid-item>
              
              <van-grid-item>
                <div class="metric-card">
                  <div class="metric-icon">
                    <van-icon name="edit" color="#faad14" :size="24" />
                  </div>
                  <div class="metric-info">
                    <div class="metric-number">{{ statistics.total_homeworks || 0 }}</div>
                    <div class="metric-label">作业总数</div>
                    <div class="metric-growth" :style="{ color: getGrowthColor(statistics.homework_growth || 0) }">
                      <van-icon :name="getGrowthIcon(statistics.homework_growth || 0)" :size="12" />
                      {{ Math.abs(statistics.homework_growth || 0) }}%
                    </div>
                  </div>
                </div>
              </van-grid-item>
              
              <van-grid-item>
                <div class="metric-card">
                  <div class="metric-icon">
                    <van-icon name="medal-o" color="#ff4d4f" :size="24" />
                  </div>
                  <div class="metric-info">
                    <div class="metric-number">{{ statistics.average_score || 0 }}</div>
                    <div class="metric-label">平均分</div>
                    <div class="metric-growth" :style="{ color: getGrowthColor(statistics.score_growth || 0) }">
                      <van-icon :name="getGrowthIcon(statistics.score_growth || 0)" :size="12" />
                      {{ Math.abs(statistics.score_growth || 0) }}%
                    </div>
                  </div>
                </div>
              </van-grid-item>
            </van-grid>
          </div>

          <!-- 活跃度统计 -->
          <div class="activity-stats">
            <van-cell-group>
              <van-cell title="活跃度统计" />
              <van-cell title="今日活跃学生" :value="statistics.daily_active_students || 0" />
              <van-cell title="本周活跃学生" :value="statistics.weekly_active_students || 0" />
              <van-cell title="本月活跃学生" :value="statistics.monthly_active_students || 0" />
              <van-cell title="平均在线时长" :value="(statistics.average_online_time || 0) + '分钟'" />
            </van-cell-group>
          </div>

          <!-- 学习进度 -->
          <div class="progress-stats">
            <van-cell-group>
              <van-cell title="学习进度" />
              <van-cell title="已完成作业" :value="statistics.completed_homeworks || 0" />
              <van-cell title="待批改作业" :value="statistics.pending_homeworks || 0" />
              <van-cell title="已完成考试" :value="statistics.completed_exams || 0" />
              <van-cell title="课程完成率" :value="(statistics.course_completion_rate || 0) + '%'" />
            </van-cell-group>
          </div>
        </div>
      </van-tab>
      
      <van-tab title="成绩分析" name="scores">
        <div class="content">
          <!-- 成绩分布 -->
          <div class="score-distribution">
            <van-cell-group>
              <van-cell title="成绩分布" />
              <van-cell title="优秀 (90-100分)" :value="statistics.score_distribution?.excellent || 0" />
              <van-cell title="良好 (80-89分)" :value="statistics.score_distribution?.good || 0" />
              <van-cell title="及格 (60-79分)" :value="statistics.score_distribution?.pass || 0" />
              <van-cell title="不及格 (0-59分)" :value="statistics.score_distribution?.fail || 0" />
            </van-cell-group>
          </div>

          <!-- 科目成绩 -->
          <div class="subject-scores">
            <van-cell-group>
              <van-cell title="各科目平均分" />
              <van-cell
                v-for="subject in statistics.subject_scores || []"
                :key="subject.name"
                :title="subject.name"
                :value="subject.average_score + '分'"
              >
                <template #right-icon>
                  <div 
                    class="score-indicator"
                    :style="{ backgroundColor: getScoreColor(subject.average_score) }"
                  ></div>
                </template>
              </van-cell>
            </van-cell-group>
          </div>

          <!-- 成绩趋势 -->
          <div class="score-trend">
            <van-cell-group>
              <van-cell title="成绩趋势" />
            </van-cell-group>
            
            <div class="trend-chart">
              <div 
                v-for="(item, index) in statistics.score_trend || []"
                :key="index"
                class="trend-item"
              >
                <div class="trend-date">{{ formatDate(item.date) }}</div>
                <div 
                  class="trend-bar"
                  :style="{ height: (item.score / 100) * 100 + 'px', backgroundColor: getScoreColor(item.score) }"
                >
                  <span class="trend-score">{{ item.score }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </van-tab>
      
      <van-tab title="学习行为" name="behavior">
        <div class="content">
          <!-- 学习时间分布 -->
          <div class="time-distribution">
            <van-cell-group>
              <van-cell title="学习时间分布" />
              <van-cell title="上午 (6:00-12:00)" :value="(statistics.time_distribution?.morning || 0) + '%'" />
              <van-cell title="下午 (12:00-18:00)" :value="(statistics.time_distribution?.afternoon || 0) + '%'" />
              <van-cell title="晚上 (18:00-24:00)" :value="(statistics.time_distribution?.evening || 0) + '%'" />
              <van-cell title="深夜 (0:00-6:00)" :value="(statistics.time_distribution?.night || 0) + '%'" />
            </van-cell-group>
          </div>

          <!-- 设备使用统计 -->
          <div class="device-stats">
            <van-cell-group>
              <van-cell title="设备使用统计" />
              <van-cell title="手机" :value="(statistics.device_stats?.mobile || 0) + '%'" />
              <van-cell title="平板" :value="(statistics.device_stats?.tablet || 0) + '%'" />
              <van-cell title="电脑" :value="(statistics.device_stats?.desktop || 0) + '%'" />
            </van-cell-group>
          </div>

          <!-- 学习习惯 -->
          <div class="study-habits">
            <van-cell-group>
              <van-cell title="学习习惯" />
              <van-cell title="平均学习时长" :value="(statistics.average_study_duration || 0) + '分钟'" />
              <van-cell title="连续学习天数" :value="statistics.continuous_study_days || 0" />
              <van-cell title="作业提交及时率" :value="(statistics.homework_on_time_rate || 0) + '%'" />
              <van-cell title="考试参与率" :value="(statistics.exam_participation_rate || 0) + '%'" />
            </van-cell-group>
          </div>
        </div>
      </van-tab>
      
      <van-tab title="排行榜" name="ranking">
        <div class="content">
          <!-- 学生排行 -->
          <div class="student-ranking">
            <van-cell-group>
              <van-cell title="学生成绩排行" />
              <van-cell
                v-for="(student, index) in statistics.student_ranking || []"
                :key="student.id"
                :title="`${index + 1}. ${student.name}`"
                :value="student.average_score + '分'"
              >
                <template #icon>
                  <van-icon 
                    v-if="index < 3" 
                    :name="index === 0 ? 'medal-o' : index === 1 ? 'medal' : 'award-o'" 
                    :color="index === 0 ? '#FFD700' : index === 1 ? '#C0C0C0' : '#CD7F32'"
                    :size="16"
                  />
                </template>
              </van-cell>
            </van-cell-group>
          </div>

          <!-- 课程热度排行 -->
          <div class="course-ranking">
            <van-cell-group>
              <van-cell title="课程热度排行" />
              <van-cell
                v-for="(course, index) in statistics.course_ranking || []"
                :key="course.id"
                :title="`${index + 1}. ${course.title}`"
                :value="course.student_count + '人学习'"
              />
            </van-cell-group>
          </div>

          <!-- 题目正确率排行 -->
          <div class="question-ranking">
            <van-cell-group>
              <van-cell title="题目正确率排行" />
              <van-cell
                v-for="(question, index) in statistics.question_ranking || []"
                :key="question.id"
                :title="`${index + 1}. ${question.content.substring(0, 20)}...`"
                :value="question.correct_rate + '%'"
              />
            </van-cell-group>
          </div>
        </div>
      </van-tab>
    </van-tabs>

    <!-- 日期选择器 -->
    <van-popup v-model:show="showDatePicker" position="bottom">
      <van-picker
        :columns="dateRangeOptions"
        @confirm="onDateRangeChange"
        @cancel="showDatePicker = false"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.data-statistics {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.date-filter {
  margin: 16px;
  border-radius: 8px;
  overflow: hidden;
}

.content {
  padding: 16px;
}

.overview-cards {
  margin-bottom: 24px;
}

.metric-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.metric-icon {
  margin-right: 12px;
}

.metric-info {
  flex: 1;
}

.metric-number {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.metric-growth {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 2px;
}

.activity-stats, .progress-stats, .score-distribution, .subject-scores, .time-distribution, .device-stats, .study-habits, .student-ranking, .course-ranking, .question-ranking {
  margin-bottom: 24px;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.score-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.score-trend {
  margin-bottom: 24px;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.trend-chart {
  display: flex;
  align-items: end;
  gap: 8px;
  height: 120px;
  padding: 20px;
  background: #f8f9fa;
  margin: 16px;
  border-radius: 8px;
}

.trend-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.trend-date {
  font-size: 10px;
  color: #666;
  margin-bottom: 8px;
  writing-mode: vertical-rl;
  text-orientation: mixed;
}

.trend-bar {
  width: 100%;
  border-radius: 4px 4px 0 0;
  position: relative;
  min-height: 20px;
  display: flex;
  align-items: end;
  justify-content: center;
}

.trend-score {
  font-size: 10px;
  color: #fff;
  font-weight: 600;
  margin-bottom: 4px;
}

:deep(.van-grid-item__content) {
  padding: 8px;
}

:deep(.van-cell__title) {
  font-weight: 500;
}

:deep(.van-cell__value) {
  font-weight: 600;
}

:deep(.van-tabs__content) {
  padding: 0;
}

:deep(.van-picker__toolbar) {
  padding: 16px;
}
</style>