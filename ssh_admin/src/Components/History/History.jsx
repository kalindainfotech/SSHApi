import axios from 'axios'
import React, { useEffect, useState } from 'react'
import { GETALLINITIATESAPI } from '../../utils/network'
import { getToken } from '../../utils/storage'
import { useNavigate } from 'react-router-dom'
import { IoMdArrowRoundBack } from "react-icons/io";

const History = () => {
    const navigate = useNavigate()
    const [status, setStatus] = useState(2)
    const [connections,setConnections] = useState([])

    const fetchConnections = async ()=>{
        await axios.get(`${GETALLINITIATESAPI}?status=${status}`).then((res)=>{
            setConnections(res.data.connections)
        }).catch((err)=>{
            console.log(err)
        })
    }
    useEffect(()=>{
        if(!getToken()){
            navigate('/')
        }
        fetchConnections()
    },[status])
  return (
    <div>
        <h1 className='backArrow'><span onClick={()=>navigate(-1)}><IoMdArrowRoundBack/> </span> History</h1>
        <select name="status" id="status" value={status} onChange={(e)=>setStatus(e.target.value)}>
            <option value="0">Rejected</option>
            <option value="1">Active</option>
            <option value="2">completed</option>
        </select>
      <table>
                <tr>
                    <th>HostName</th>
                    <th>Requester</th>
                    <th>Date & Time</th>
                    <th>Status</th>
                </tr>
                {connections ? connections.map((connection,index) => (
                    <tr key={index}>
                        <td>{connection.hostname}</td>
                        <td>{connection.requester}</td>
                        <td>{connection.created_at}</td>
                        <td style={{color:connection.status===2?"green":connection.status===1?"blue":"red"}}>{connection.status===2?"completed":connection.status===1?"active":"rejected"}</td>
                    </tr>)) : ""}
            </table>
    </div>
  )
}

export default History
