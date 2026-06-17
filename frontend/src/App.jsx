import { BrowserRouter, Routes, Route } from 'react-router-dom'

function App() {
  return (
    <BrowserRouter basename="/react">
      <div className="app">
        <h1>Stock Management System（React）</h1>
        <Routes>
          <Route path="/" element={<div>ホームページ</div>} />
          <Route path="/goods" element={<div>商品一覧（準備中）</div>} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App