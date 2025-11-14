import { BrowserRouter, Routes, Route } from "react-router-dom";
import Panchang from './Panchang/Panchang.jsx';

function App(){
  return(
    <BrowserRouter>
    <Routes>
      <Route path="/" element={<Panchang/>}></Route>
    </Routes>
  </BrowserRouter>
  )
}

export default App;