import { Component } from 'react'

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          padding: '24px',
          background: 'var(--background)',
          color: 'var(--foreground)',
        }}>
          <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '12px' }}>页面出错了</h2>
          <p style={{ fontSize: '14px', color: 'var(--muted-foreground)', marginBottom: '24px' }}>
            发生了意外错误，请刷新页面重试
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '8px 24px',
              borderRadius: '6px',
              border: '1px solid var(--border)',
              background: 'var(--primary)',
              color: 'var(--primary-foreground)',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            刷新页面
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
