import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X } from 'lucide-react';

const ConfirmModal = ({ isOpen, onClose, onConfirm, title, message, confirmText = 'Delete', type = 'danger' }) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="modal-overlay" onClick={onClose}>
          <motion.div 
            className="modal-content"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            onClick={e => e.stopPropagation()}
            style={{ maxWidth: '400px' }}
          >
            <button 
              className="btn btn-ghost" 
              onClick={onClose} 
              style={{ position: 'absolute', right: '1rem', top: '1rem', padding: '0.25rem' }}
            >
              <X size={20} />
            </button>

            <div className={`confirm-modal-icon ${type}`}>
              <AlertTriangle size={32} />
            </div>

            <h2 className="confirm-modal-title">{title}</h2>
            <p className="confirm-modal-message">{message}</p>

            <div style={{ display: 'flex', gap: '1rem' }}>
              <button 
                className="btn btn-ghost" 
                style={{ flex: 1, justifyContent: 'center' }} 
                onClick={onClose}
              >
                Cancel
              </button>
              <button 
                className={`btn ${type === 'danger' ? 'btn-danger' : 'btn-primary'}`} 
                style={{ flex: 1, justifyContent: 'center', background: type === 'danger' ? 'var(--danger)' : 'var(--primary)', color: 'white' }} 
                onClick={() => {
                  onConfirm();
                  onClose();
                }}
              >
                {confirmText}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default ConfirmModal;
