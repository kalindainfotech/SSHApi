import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Button } from '@mui/material';
import sound from '../../assets/sound/sound.mp3'
import { GETALLINITIATESAPI, UPLOADAPI } from '../../utils/network';


const ApproveScreen = () => {
    const [connections, setConnections] = useState([]);
    const [loading, setLoading] = useState(true);

    const prevConnectionsLength = useRef(connections.length);

    const fetchConnections = async () => {
        try {
            const response = await axios.get(GETALLINITIATESAPI);
            console.log(response.data.connections)
            setConnections(response.data.connections);
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
        try {
            await axios.put(UPLOADAPI, {
                session_id,
                action,
            });
            // alert(response.data.status);
            fetchConnections();
        } catch (error) {
            console.error('Error handling connection:', error);
            alert('Failed to process the action');
        }
    };
    return (
        <div>
            <h1>SSH approval from clients</h1>
            <table>
                <tr>
                    <th>HostName</th>
                    <th>Requester</th>
                    <th></th>
                </tr>
                {connections ? connections.map((connection) => (
                    <tr>
                        <td>{connection.hostname}</td>
                        <td>{connection.requester}</td>
                        <td>
                            <Button variant="contained" color='success' onClick={() => handleConnectionAction(connection.session_id, 'approve')}>Approve</Button>
                            <Button variant="contained" color='error' onClick={() => handleConnectionAction(connection.session_id, 'reject')}>Reject</Button>
                        </td>
                    </tr>
                )) : ''}
            </table>
        </div>
    )
}

export default ApproveScreen
