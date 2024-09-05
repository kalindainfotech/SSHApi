import React, { useState } from 'react'
import axios from 'axios';
import { ToastContainer, toast } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css';
import './Login.css'
import { useNavigate } from 'react-router-dom';
import { LOGINAPI, USERSAPI } from '../../utils/network';
import { setToken } from '../../utils/storage';

const Login = () => {
    const navigate = useNavigate()
    const [credetials, setCredentials] = useState({ username: "", password: "" })

    const handleLogin = async () => {
        console.log("clicked")
        await axios.post(LOGINAPI,credetials).then(async (res)=>{
            if(res.data.status === 200){
                setToken(res.data.login_session_id)
                await axios.get(USERSAPI).then(()=>{
                    navigate("/approval")    
                }).catch((err)=>console.log(err))
            }else{
                toast.error("Invalid Username and Password")
            }
        }).catch((err)=>console.log(err))
    }
    return (
        <div>
            <div className='login'>
                <ToastContainer />
                <div className='login-content'>
                    <div className='login-textbox'>
                        <label htmlFor="email">Email</label>
                        <input type="text" name="username" id="username" value={credetials.username} onChange={(e) => setCredentials({ ...credetials, [e.target.name]: e.target.value })} placeholder='Enter the Username' />
                    </div>
                    <div className='login-textbox'>
                        <label htmlFor="password">Password</label>
                        <input type="password" name="password" id="password" value={credetials.password} onChange={(e) => setCredentials({ ...credetials, [e.target.name]: e.target.value })} placeholder='Enter the Password' />
                    </div>
                    <input type="button" value="Login" onClick={handleLogin} />
                </div>
            </div>
        </div>
    )
}

export default Login
