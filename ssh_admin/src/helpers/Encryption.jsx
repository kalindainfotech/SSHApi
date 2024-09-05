import CryptoJS from "crypto-js";

const password = "SshManager@123"

export let encrypt = (textToConvert) => {
    return  CryptoJS.AES.encrypt(
      textToConvert.trim(),
      password.trim()
    ).toString();
  };

  export let decrypt = (textToConvert) => {
    return  CryptoJS.AES.decrypt(
      textToConvert.trim(),
      password.trim()
    ).toString(CryptoJS.enc.Utf8);
  };