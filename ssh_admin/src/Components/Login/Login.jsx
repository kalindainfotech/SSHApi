import React, { useState } from 'react'

import { ToastContainer, toast } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css';
import './Login.css'
import { useNavigate } from 'react-router-dom';

const Login = () => {
    const navigate = useNavigate()
    const [credetials, setCredentials] = useState({ email: "", password: "" })

    const handleLogin = () => {
        console.log("clicked")
        navigate("/approval")
    }
    return (
        <div>
            <div className='login'>
                <ToastContainer />
                <div className='login-content'>
                    <div className='login-textbox'>
                        <label htmlFor="email">Email</label>
                        <input type="text" name="email" id="email" value={credetials.email} onChange={(e) => setCredentials({ ...credetials, [e.target.name]: e.target.value })} placeholder='Enter the email' />
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
