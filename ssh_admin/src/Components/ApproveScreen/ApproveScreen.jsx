import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Button } from '@mui/material';
import sound from '../../assets/sound/sound.mp3';
import { GETALLINITIATESAPI, UPLOADAPI } from '../../utils/network';
import { getToken, Logout } from '../../utils/storage';
import { useNavigate } from 'react-router-dom';
import { FaHistory } from "react-icons/fa";
import { IoMdArrowRoundBack } from 'react-icons/io';

const ApproveScreen = () => {
    const navigate = useNavigate();
    const [connections, setConnections] = useState([]);
    const [loading, setLoading] = useState(true);
    const [popup, setPopup] = useState(false);
    const [confirmPopup, setConfirmPopup] = useState(false)
    const [confirm, setConfirm] = useState(false)

    const prevConnectionsLength = useRef(connections.length);

    const fetchConnections = async () => {
        try {
            if (getToken()) {
                const response = await axios.get(GETALLINITIATESAPI);
                setConnections(response.data.connections);
            } else {
                navigate('/');
            }
        } catch (error) {
            console.error('Error fetching connections:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchConnections();
        const intervalId = setInterval(fetchConnections, 5000);
        return () => clearInterval(intervalId);
    }, []);

    useEffect(() => {
        if (connections.length !== prevConnectionsLength.current) {
            const alertSound = new Audio(sound);
            alertSound.play().catch((error) => console.error('Error playing alert sound:', error));
            prevConnectionsLength.current = connections.length;
        }
    }, [connections]);

    const handleConnectionAction = async (session_id, action) => {

        // if(!confirm){
        //     setConfirmPopup(!confirmPopup)
        // }else{
            try {
                await axios.put(UPLOADAPI, { session_id, action });
                fetchConnections();
                setConfirm(!confirm)
            } catch (error) {
                console.error('Error handling connection:', error);
                setConfirm(!confirm)
            }
        // }

        
    };

    const handleLogout = () => {
        Logout();
        navigate('/');
    };

    return (
        <div className='ApprovalScreen'>
            <div className='ApprovalscreenHeader'>
                <h1>
                    <span onClick={() => navigate(-1)}><IoMdArrowRoundBack /> </span>
                    SSH approval from clients
                </h1>
                <div className='ApprovalscreenHeader1'>
                    <FaHistory onClick={() => navigate('/history')} />
                    <Button variant='contained' onClick={() => setPopup(!popup)}>Logout</Button>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>HostName</th>
                        <th>Requester</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {connections && connections.length > 0 ? connections.map((connection) => (
                        <tr key={connection.session_id}>
                            <td>{connection.hostname}</td>
                            <td>{connection.requester}</td>
                            <td>
                                <Button
                                    variant="contained"
                                    style={{ marginRight: "25px" }}
                                    color='success'
                                    onClick={() => handleConnectionAction(connection.session_id, 'approve')}
                                >
                                    Approve
                                </Button>
                                <Button
                                    variant="contained"
                                    color='error'
                                    onClick={() => handleConnectionAction(connection.session_id, 'reject')}
                                >
                                    Reject
                                </Button>
                            </td>
                        </tr>
                    )) : (
                        <tr>
                            <td colSpan="3" style={{ textAlign: 'center' }}>No connections available</td>
                        </tr>
                    )}
                </tbody>
            </table>
            {popup && (
                <div className="popupScreen">
                    <div className="popupScreens">
                        <h2>!Alert</h2>
                        <p>Please Confirm to logout</p>
                        <div className="popupScreen-button">
                            <Button variant="outlined" color="error" onClick={() => setPopup(!popup)}>No, Cancel</Button>
                            <Button variant="contained" color="success" onClick={handleLogout}>Yes, Confirm</Button>
                        </div>
                    </div>
                </div>
            )}

            {confirmPopup && (
                <div className="popupScreen">
                    <div className="popupScreens">
                        <h2>!Alert</h2>
                        <p>Please Confirm to logout</p>
                        <div className="popupScreen-button">
                            <Button variant="outlined" color="error" onClick={() => setConfirmPopup(!confirmPopup)}>No, Cancel</Button>
                            <Button variant="contained" color="success" onClick={()=>setConfirm(!confirm)}>Yes, Confirm</Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ApproveScreen;
