import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'http://localhost:8000/api', // or your deployed backend
  headers: {
    Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
  },
});

export default axiosInstance;