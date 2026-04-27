declare module 'react-quill' {
  import React from 'react'

  interface QuillOptions {
    theme?: string
    modules?: Record<string, unknown>
    formats?: string[]
    bounds?: string | HTMLElement
    scrollingContainer?: string | HTMLElement
    tabIndex?: number
  }

  interface ReactQuillProps extends QuillOptions {
    id?: string
    className?: string
    style?: React.CSSProperties
    value?: string
    defaultValue?: string
    readOnly?: boolean
    placeholder?: string
    onChange?: (
      value: string,
      delta: unknown,
      source: string,
      editor: unknown
    ) => void
    onChangeSelection?: (
      selection: unknown,
      source: string,
      editor: unknown
    ) => void
    onFocus?: (selection: unknown, source: string, editor: unknown) => void
    onBlur?: (previousSelection: unknown, source: string, editor: unknown) => void
    onKeyPress?: React.EventHandler<React.KeyboardEvent<HTMLDivElement>>
    onKeyDown?: React.EventHandler<React.KeyboardEvent<HTMLDivElement>>
    onKeyUp?: React.EventHandler<React.KeyboardEvent<HTMLDivElement>>
    preserveWhitespace?: boolean
  }

  const ReactQuill: React.ForwardRefExoticComponent<
    ReactQuillProps & React.RefAttributes<unknown>
  >

  export default ReactQuill
}
