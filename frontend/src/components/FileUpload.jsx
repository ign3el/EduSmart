import { useCallback, useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import { FiUploadCloud, FiFile } from 'react-icons/fi'
import './FileUpload.css'

function FileUpload({ onUpload, gradeLevel, onGradeLevelChange, isReuploading }) {
  const fileInputRef = useRef(null)

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      onUpload(acceptedFiles[0])
    }
  }, [onUpload])

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc']
    },
    maxFiles: 1
  })

  return (
    <div className="file-upload">
      <h2>📄 Upload Learning Material</h2>
      <p className="subtitle">Upload a PDF or Word document to get started</p>

      <div className="grade-selector">
        <label htmlFor="grade">Select Grade Level:</label>
        <select 
          id="grade" 
          value={gradeLevel} 
          onChange={(e) => onGradeLevelChange(parseInt(e.target.value))}
        >
          <option value={1}>KG-1 / Grade 1</option>
          <option value={2}>Grade 2</option>
          <option value={3}>Grade 3</option>
          <option value={4}>Grade 4</option>
          <option value={5}>Grade 5</option>
          <option value={6}>Grade 6</option>
          <option value={7}>Grade 7</option>
        </select>
      </div>

      <div 
        {...getRootProps()} 
        className={`dropzone ${isDragActive ? 'active' : ''}`}
      >
        <input {...getInputProps()} />
        <FiUploadCloud className="upload-icon" />
        {isDragActive ? (
          <p>Drop your file here...</p>
        ) : (
          <>
            <p>Drag & drop a file here, or click to browse</p>
            <span className="file-types">PDF, DOCX, DOC</span>
          </>
        )}
      </div>

      {acceptedFiles.length > 0 && (
        <div className="file-preview">
          <FiFile />
          <span>{acceptedFiles[0].name}</span>
          <span className="file-size">
            ({(acceptedFiles[0].size / 1024 / 1024).toFixed(2)} MB)
          </span>
        </div>
      )}
    </div>
  )
}

export default FileUpload
