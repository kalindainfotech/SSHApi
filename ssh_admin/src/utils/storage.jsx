import { decrypt, encrypt } from "../helpers/Encryption"

export function setToken(data) {
    localStorage.setItem('token', encrypt(data))
}

export function getToken() {
    return decrypt(localStorage.getItem('token'))
}

export function Logout(){
    localStorage.clear()
}