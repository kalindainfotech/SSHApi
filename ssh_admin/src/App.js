import React from 'react';
import './App.css'
import ApproveScreen from './Components/ApproveScreen/ApproveScreen';
import Login from './Components/Login/Login';
import { Route, HashRouter as Router, Routes } from 'react-router-dom';
import History from './Components/History/History';

function App() {
  
  return (
    <div className="App">
      <Router>
        <Routes>
          <Route path='/' element={<Login/>}></Route>
          <Route path='/approval' element={<ApproveScreen/>}></Route>
          <Route path='/history' element={<History/>}></Route>
        </Routes>
      </Router>
    </div>
  );
}

export default App;
