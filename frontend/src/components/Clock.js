import { useState, useEffect } from 'react';

function Clock() {
  const [date, setDate] = useState(new Date());

  function refreshClock() {
    setDate(new Date());
  }

  useEffect(() => {
    const timerId = setInterval(refreshClock, 1000);
    return function cleanup() {
      clearInterval(timerId);
    };
  }, []);

  const days = ['domenica', 'lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì', 'sabato']

  function formatClock(value) {
    return ('0' + value).slice(-2)
  }

  const day = days[date.getDay()]
  const date_num = formatClock(date.getDate())
  const month = formatClock(date.getMonth() + 1)
  const h = formatClock(date.getHours())
  const m =formatClock(date.getMinutes())
  const s = formatClock(date.getSeconds())

  return (
    <div>
      <div id='clock_time'>{h}:{m}</div>
      <div id='clock_sec'>{s}</div>
      <div id='clock_date'>{day}, {date_num}.{month}</div>
    </div>
  )
}
export default Clock;
