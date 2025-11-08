import './App.css'
import background from './assets/video.mp4'
import axios from 'axios';

async function fetchPanchang() {
  try {
    const response = await axios.get('/logic/', {
      params: {
        date: "2025-11-14",
        time: "10:30",
        timezone: "Asia/Kolkata"
      }
    });
    console.log(response.data);
  } catch (error) {
    console.error("Error fetching Panchang:", error);
  }
}

function App() {
  return (
    <>
      <video src={background} muted autoPlay loop></video>
      <h1>कालरूपाय नमः शिवाय||</h1>
      <button onClick={fetchPanchang}>Fetch Panchang</button>
    </>
  );
}

export default App;
