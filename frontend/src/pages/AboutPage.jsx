import { useEffect, useState } from 'react'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function AboutPage() {
  const [content, setContent] = useState('')

  useEffect(() => {
    fetch('/ABOUT.md').then((r) => r.text()).then(setContent).catch(() => setContent('无法加载关于信息'))
  }, [])

  const renderMarkdown = (md) => {
    let html = md
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`(.+?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br/>')
    return html
  }

  return (
    <>
      <Header>
        <h1 className='text-lg font-medium'>关于</h1>
      </Header>
      <Main>
        <Card>
          <CardHeader>
            <CardTitle>关于 EmbyQ</CardTitle>
            <CardDescription>系统信息</CardDescription>
          </CardHeader>
          <CardContent>
            <div className='prose prose-sm dark:prose-invert max-w-none' dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }} />
          </CardContent>
        </Card>
      </Main>
    </>
  )
}
