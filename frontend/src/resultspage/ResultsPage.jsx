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