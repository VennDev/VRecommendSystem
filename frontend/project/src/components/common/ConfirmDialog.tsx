import React from 'react';
import { AlertTriangle, Info, Trash2, Edit } from 'lucide-react';

export interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  type?: 'delete' | 'update' | 'warning' | 'info';
  confirmText?: string;
  cancelText?: string;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  type = 'warning',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
}) => {
  if (!isOpen) return null;

  const getIcon = () => {
    switch (type) {
      case 'delete':
        return <Trash2 className="h-6 w-6 text-error" />;
      case 'update':
        return <Edit className="h-6 w-6 text-warning" />;
      case 'info':
        return <Info className="h-6 w-6 text-info" />;
      default:
        return <AlertTriangle className="h-6 w-6 text-warning" />;
    }
  };

  const getButtonClass = () => {
    switch (type) {
      case 'delete':
        return 'btn-error';
      case 'update':
        return 'btn-warning';
      default:
        return 'btn-primary';
    }
  };

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <div className="modal modal-open">
      <div className="modal-box">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">{getIcon()}</div>
          <div className="flex-1">
            <h3 className="font-bold text-lg mb-2">{title}</h3>
            <p className="text-sm opacity-80">{message}</p>
          </div>
        </div>
        <div className="modal-action">
          <button onClick={onClose} className="btn btn-ghost">
            {cancelText}
          </button>
          <button onClick={handleConfirm} className={`btn ${getButtonClass()}`}>
            {confirmText}
          </button>
        </div>
      </div>
      <div className="modal-backdrop" onClick={onClose}></div>
    </div>
  );
};
