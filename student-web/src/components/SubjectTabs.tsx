import React from 'react'
import { Tag } from 'antd'

interface SubjectTabsProps {
  subjects: string[]
  activeSubject: string | null
  onChange: (subject: string | null) => void
  showAll?: boolean
}

const SubjectTabs: React.FC<SubjectTabsProps> = ({
  subjects,
  activeSubject,
  onChange,
  showAll = true,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        gap: 8,
        overflowX: 'auto',
        padding: '8px 0',
        WebkitOverflowScrolling: 'touch',
      }}
    >
      {showAll && (
        <Tag
          color={activeSubject === null ? '#2563EB' : undefined}
          onClick={() => onChange(null)}
          style={{ cursor: 'pointer', flexShrink: 0, margin: 0 }}
        >
          全部
        </Tag>
      )}
      {subjects.map((subject) => (
        <Tag
          key={subject}
          color={activeSubject === subject ? '#2563EB' : undefined}
          onClick={() => onChange(subject)}
          style={{ cursor: 'pointer', flexShrink: 0, margin: 0 }}
        >
          {subject}
        </Tag>
      ))}
    </div>
  )
}

export default SubjectTabs
