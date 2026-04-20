export function AuthLayout({ children }) {
  return (
    <div className='container grid h-svh max-w-none items-center justify-center'>
      <div className='mx-auto flex w-full flex-col justify-center space-y-2 py-8 sm:w-[480px] sm:p-8'>
        <div className='mb-4 flex items-center justify-center'>
          <img src='/logo.svg' alt='EmbyQ' className='h-[50px]' />
        </div>
        {children}
      </div>
    </div>
  )
}
