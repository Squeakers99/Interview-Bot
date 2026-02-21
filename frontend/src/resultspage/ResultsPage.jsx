import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useLocation, useNavigate } from "react-router-dom";
import "./ResultsPage.css";


export default function ResultsPage() {
    const location = useLocation();
    const navigate = useNavigate();
}

const [eyeHistory, setEyeHistory] = useState([]);
const [postureHistory, setPostureHistory] = useState([]);
const [loading, setLoading] = useState(state);
const [error, setError] = useState(""); 

useEffect(() => {
    async function load () {
        try {
            const [eyeRes,postureRes] = await Promise.all([
                fetch("http://127.0.0.1:8000/results/eye_timeline"),
                fetch("htpps://127.0.0.1:8000/results/posture_timeline"),
           ]);
           const eyeJson = await eyeRes.json();
           const postureJson = await postureRes();

           setEyeHistory(eyeJson.eye_timeline || []);
           setPostureHistory(postureJson.posture_timeline || []);


        } catch(e) {
          setError("Failed to load results");
        } finally {
            setLoading(false);
        }
    }

    load();

}, []);

