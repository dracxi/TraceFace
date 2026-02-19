import React from 'react';
import { useToast } from '../contexts/ToastContext';

const Toast: React.FC = () => {
  const { toasts, removeToast } = useToast();

  const getToastStyles = (type: string) => {
    const baseStyles = 'px-4 py-3 rounded-lg shadow-lg flex items-center justify-between min-w-[300px] max-w-[500px] mb-2 animate-slide-in';
    
    switch (type) {
      case 'success':
        return `${baseStyles} bg-green-500 text-white`;
      case 'error':
        return `${baseStyles} bg-red-500 text-white`;
      case 'warning':
        return `${baseStyles} bg-yellow-500 text-white`;
      case 'info':
        return `${baseStyles} bg-blue-500 text-white`;
      default:
        return `${baseStyles} bg-gray-500 text-white`;
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col">
      {toasts.map((toast) => (
        <div key={toast.id} className={getToastStyles(toast.type)}>
          <span className="flex-1">{toast.message}</span>
          <button
            onClick={() => removeToast(toast.id)}
            className="ml-4 text-white hover:text-gray-200 font-bold"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
};

export default Toast;
