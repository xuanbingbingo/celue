import React from 'react';

function Toast({ show, message }) {
  if (!show) return null;

  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 bg-slate-800 text-white px-6 py-3 rounded-xl shadow-2xl z-50 animate-fade-in">
      {message}
    </div>
  );
}

export default Toast;
