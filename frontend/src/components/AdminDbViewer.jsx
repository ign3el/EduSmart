import React, { useState, useEffect } from 'react';
import { getJobStateDbTables, getJobStateTableData } from '../../services/api';
import './AdminDbViewer.css';

const AdminDbViewer = ({ onBack }) => {
    const [tables, setTables] = useState([]);
    const [selectedTable, setSelectedTable] = useState('');
    const [tableData, setTableData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [headers, setHeaders] = useState([]);

    useEffect(() => {
        const fetchTables = async () => {
            try {
                setError('');
                setLoading(true);
                const response = await getJobStateDbTables();
                setTables(response.tables || []);
                if (response.tables && response.tables.length > 0) {
                    // Automatically select the first table
                    handleTableSelect(response.tables[0]);
                }
            } catch (err) {
                setError(err.message || 'Failed to fetch tables.');
            } finally {
                setLoading(false);
            }
        };
        fetchTables();
    }, []);

    const handleTableSelect = async (tableName) => {
        if (!tableName) return;

        setSelectedTable(tableName);
        try {
            setError('');
            setLoading(true);
            const response = await getJobStateTableData(tableName);
            const content = response.content || [];
            setTableData(content);

            if (content.length > 0) {
                // Get headers from the first object, excluding long content
                const firstRow = content[0];
                const filteredHeaders = Object.keys(firstRow).filter(key => {
                    const value = firstRow[key];
                    return typeof value !== 'string' || value.length < 100;
                });
                setHeaders(filteredHeaders);
            } else {
                setHeaders([]);
            }

        } catch (err) {
            setError(err.message || `Failed to fetch data for table ${tableName}.`);
            setTableData([]);
            setHeaders([]);
        } finally {
            setLoading(false);
        }
    };
    
    const renderCellContent = (item, header) => {
        const value = item[header];
        if (typeof value === 'boolean') {
            return <span className={value ? 'bool-true' : 'bool-false'}>{String(value)}</span>;
        }
        if (value === null || typeof value === 'undefined') {
            return <span className="null-value">NULL</span>;
        }
        // Truncate long strings
        const stringValue = String(value);
        if (stringValue.length > 50) {
            return <span title={stringValue}>{stringValue.substring(0, 50)}...</span>
        }
        return stringValue;
    };

    return (
        <div className="admin-db-viewer">
            <header className="db-viewer-header">
                <div className="db-viewer-header-top">
                    <h1>Job State DB Viewer</h1>
                    <button onClick={onBack} className="back-button">← Back to Admin</button>
                </div>
                <p>A read-only view of the <code>job_state.db</code> SQLite database.</p>
            </header>

            <div className="controls">
                <label htmlFor="table-select">Select a Table:</label>
                <select 
                    id="table-select"
                    value={selectedTable}
                    onChange={(e) => handleTableSelect(e.target.value)}
                    disabled={loading}
                >
                    <option value="">-- Select --</option>
                    {tables.map(table => (
                        <option key={table} value={table}>{table}</option>
                    ))}
                </select>
            </div>

            {loading && <div className="loader">Loading...</div>}
            {error && <div className="error-message">{error}</div>}

            <div className="table-container">
                {tableData.length > 0 ? (
                    <table>
                        <thead>
                            <tr>
                                {headers.map(header => (
                                    <th key={header}>{header}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {tableData.map((item, index) => (
                                <tr key={item.id || item.story_id || item.scene_id || index}>
                                    {headers.map(header => (
                                        <td key={header}>{renderCellContent(item, header)}</td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    !loading && <p className="no-data">No data to display for the selected table.</p>
                )}
            </div>
        </div>
    );
};

export default AdminDbViewer;
