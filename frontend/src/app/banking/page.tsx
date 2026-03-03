"use client";

import React, { useState } from 'react';
import { Typography, Steps, Button, Upload, Card, message, Space, Alert, Table, Tag, Select, Row, Col, Tabs, Input, Spin, List } from 'antd';
import { InboxOutlined, DownloadOutlined, CheckCircleOutlined, CloudUploadOutlined, RetweetOutlined, FilePdfOutlined, FileExcelOutlined, WarningOutlined, LockOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

const { Title, Text } = Typography;
const { Dragger } = Upload;

export default function BankingImportPage() {
    const [current, setCurrent] = useState(0);
    const [uploadMode, setUploadMode] = useState<'excel' | 'pdf'>('excel');

    // ---------- PDF state ----------
    const [pdfPassword, setPdfPassword] = useState('');
    const [pdfParsing, setPdfParsing] = useState(false);
    const [pdfResult, setPdfResult] = useState<any>(null);
    const [pdfWarnings, setPdfWarnings] = useState<string[]>([]);

    const next = () => setCurrent(current + 1);
    const prev = () => setCurrent(current - 1);

    // ---------- Excel upload ----------
    const excelUploadProps: UploadProps = {
        name: 'file',
        multiple: false,
        accept: '.csv,.xlsx,.xls',
        action: '/api/tally/upload',
        onChange(info) {
            const { status } = info.file;
            if (status === 'done') {
                message.success(`${info.file.name} uploaded successfully.`);
                next();
            } else if (status === 'error') {
                message.error(`${info.file.name} upload failed.`);
            }
        },
    };

    // ---------- PDF upload ----------
    const handlePdfUpload = async (file: File) => {
        setPdfParsing(true);
        setPdfResult(null);
        setPdfWarnings([]);

        const formData = new FormData();
        formData.append('file', file);
        if (pdfPassword) {
            formData.append('password', pdfPassword);
        }

        try {
            const res = await fetch('/api/tally/upload-pdf', {
                method: 'POST',
                body: formData,
            });
            console.log('[PDF Upload] Response status:', res.status);
            const data = await res.json();
            console.log('[PDF Upload] Response data:', data);
            if (data.success) {
                setPdfResult(data);
                setPdfWarnings(data.warnings || []);
                message.success(`Extracted ${data.row_count} transactions from ${data.bank_detected}`);
                next();
            } else {
                message.error(data.message || 'Failed to parse PDF');
                setPdfWarnings(data.warnings || []);
            }
        } catch (err: any) {
            console.error('[PDF Upload] Error:', err);
            message.error(`Upload failed: ${err?.message || 'Network error'}`);
        } finally {
            setPdfParsing(false);
        }

        return false; // Prevent Ant upload default behavior
    };

    // Placeholder dummy data for Excel flow
    const dummyData = [
        { key: '1', date: '2024-03-20', narration: 'UPI/ZOMATO/FOOD', debit: 450, credit: 0, mapped: 'Staff Welfare', type: 'Payment', status: 'Mapped' },
        { key: '2', date: '2024-03-21', narration: 'NEFT UBER INDIA', debit: 1200, credit: 0, mapped: '', type: 'Payment', status: 'Unmapped' },
        { key: '3', date: '2024-03-21', narration: 'CASH DEPOSIT', debit: 0, credit: 50000, mapped: 'Cash A/c', type: 'Receipt', status: 'Mapped' },
    ];

    const previewColumns = [
        { title: 'Date', dataIndex: 'Date', width: 100 },
        { title: 'Narration', dataIndex: 'Narration', width: 300, ellipsis: true },
        {
            title: 'Type',
            key: 'type',
            width: 80,
            render: (_: any, record: any) => {
                const t = record.Debit > 0 ? 'Payment' : 'Receipt';
                return <Tag color={t === 'Receipt' ? 'green' : 'red'}>{t}</Tag>;
            }
        },
        {
            title: 'Amount',
            key: 'amount',
            width: 120,
            render: (_: any, record: any) => {
                const amt = record.Debit > 0 ? record.Debit : record.Credit;
                return `₹${Number(amt).toLocaleString('en-IN')}`;
            }
        },
    ];

    const fullColumns = [
        ...previewColumns,
        {
            title: 'Suggested Ledger',
            dataIndex: 'mapped',
            width: 200,
            render: (mapped: string) => (
                <Select
                    style={{ width: '100%' }}
                    defaultValue={mapped || undefined}
                    placeholder="Select ledger"
                    options={[
                        { value: 'Staff Welfare', label: 'Staff Welfare' },
                        { value: 'Conveyance', label: 'Conveyance' },
                        { value: 'Cash A/c', label: 'Cash A/c' },
                        { value: 'Bank Suspense A/c (Default)', label: 'Bank Suspense A/c (Default)' }
                    ]}
                />
            )
        },
    ];

    const steps = [
        {
            title: 'Upload File',
            content: (
                <Card variant="borderless" style={{ marginTop: 24 }}>
                    <Tabs
                        activeKey={uploadMode}
                        onChange={(key) => setUploadMode(key as 'excel' | 'pdf')}
                        centered
                        items={[
                            {
                                key: 'excel',
                                label: <span><FileExcelOutlined /> Excel / CSV Upload</span>,
                                children: (
                                    <div style={{ marginTop: 16 }}>
                                        <div style={{ textAlign: 'center', marginBottom: 16 }}>
                                            <Title level={4}>Import Bank Statement (Excel)</Title>
                                            <Text type="secondary">Upload your CSV or Excel file.</Text>
                                        </div>
                                        <Dragger {...excelUploadProps} style={{ padding: '40px 0' }}>
                                            <p className="ant-upload-drag-icon">
                                                <InboxOutlined style={{ color: '#1677ff', fontSize: 48 }} />
                                            </p>
                                            <p className="ant-upload-text" style={{ fontSize: 18, fontWeight: 500 }}>Click or drag CSV/XLSX file</p>
                                        </Dragger>
                                    </div>
                                ),
                            },
                            {
                                key: 'pdf',
                                label: <span><FilePdfOutlined /> PDF Upload <Tag color="blue" style={{ marginLeft: 4 }}>Beta</Tag></span>,
                                children: (
                                    <div style={{ marginTop: 16 }}>
                                        <div style={{ textAlign: 'center', marginBottom: 16 }}>
                                            <Title level={4}>Import Bank Statement (PDF)</Title>
                                            <Text type="secondary">Upload any Indian bank PDF statement. Supports HDFC, SBI, ICICI, and more.</Text>
                                        </div>

                                        <div style={{ maxWidth: 400, margin: '0 auto 24px' }}>
                                            <Input.Password
                                                prefix={<LockOutlined />}
                                                placeholder="PDF password (leave blank if none)"
                                                value={pdfPassword}
                                                onChange={(e) => setPdfPassword(e.target.value)}
                                                style={{ marginBottom: 16 }}
                                            />
                                        </div>

                                        <Spin spinning={pdfParsing} tip="Parsing PDF... this may take a moment">
                                            <Dragger
                                                name="file"
                                                multiple={false}
                                                accept=".pdf"
                                                beforeUpload={(file) => { handlePdfUpload(file); return false; }}
                                                showUploadList={false}
                                                style={{ padding: '40px 0' }}
                                            >
                                                <p className="ant-upload-drag-icon">
                                                    <FilePdfOutlined style={{ color: '#cf1322', fontSize: 48 }} />
                                                </p>
                                                <p className="ant-upload-text" style={{ fontSize: 18, fontWeight: 500 }}>Click or drag PDF file</p>
                                                <p className="ant-upload-hint" style={{ color: '#888' }}>
                                                    Native/digital PDFs work best. Scanned PDFs require Tesseract OCR on server.
                                                </p>
                                            </Dragger>
                                        </Spin>

                                        {pdfWarnings.length > 0 && (
                                            <Alert
                                                message="Parser Warnings"
                                                description={
                                                    <List
                                                        size="small"
                                                        dataSource={pdfWarnings}
                                                        renderItem={(w) => <List.Item><WarningOutlined style={{ color: '#faad14', marginRight: 8 }} />{w}</List.Item>}
                                                    />
                                                }
                                                type="warning"
                                                showIcon
                                                style={{ marginTop: 16 }}
                                            />
                                        )}
                                    </div>
                                ),
                            },
                        ]}
                    />
                </Card>
            ),
        },
        {
            title: 'Validate & Preview',
            content: (
                <Card variant="borderless" style={{ marginTop: 24 }}>
                    {pdfResult && (
                        <Alert
                            message={`✅ Extracted ${pdfResult.row_count} transactions from ${pdfResult.bank_detected}`}
                            description={`Pages: ${pdfResult.stats?.total_pages || '?'} | Rows: ${pdfResult.stats?.total_rows || '?'}`}
                            type="success"
                            showIcon
                            style={{ marginBottom: 16 }}
                        />
                    )}
                    {pdfWarnings.length > 0 && (
                        <Alert
                            message={`${pdfWarnings.length} warnings`}
                            type="warning"
                            showIcon
                            closable
                            style={{ marginBottom: 16 }}
                        />
                    )}
                    <Table
                        dataSource={(pdfResult?.preview || dummyData).map((r: any, i: number) => ({ ...r, key: i }))}
                        columns={previewColumns}
                        pagination={false}
                        size="small"
                        scroll={{ y: 350 }}
                    />
                    <div style={{ marginTop: 24, textAlign: 'right' }}>
                        <Button onClick={prev} style={{ marginRight: 8 }}>Back</Button>
                        <Button type="primary" onClick={next}>Proceed to Map Ledgers</Button>
                    </div>
                </Card>
            ),
        },
        {
            title: 'Map Ledgers',
            content: (
                <Card variant="borderless" style={{ marginTop: 24 }}>
                    <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
                        <Col><Text strong>Review AI Suggested Mappings</Text></Col>
                        <Col>
                            <Space>
                                <Button icon={<RetweetOutlined />}>Auto Map</Button>
                                <Select defaultValue="All" style={{ width: 120 }} options={[{ value: 'All', label: 'All' }, { value: 'Unmapped', label: 'Unmapped' }]} />
                            </Space>
                        </Col>
                    </Row>
                    <Table
                        dataSource={(pdfResult?.preview || dummyData).map((r: any, i: number) => ({ ...r, key: i }))}
                        columns={fullColumns}
                        pagination={false}
                        size="small"
                        scroll={{ x: 800, y: 350 }}
                    />
                    <div style={{ marginTop: 24, textAlign: 'right' }}>
                        <Button onClick={prev} style={{ marginRight: 8 }}>Back</Button>
                        <Button type="primary" onClick={next}>Confirm & Proceed</Button>
                    </div>
                </Card>
            ),
        },
        {
            title: 'Generate XML',
            content: (
                <Card variant="borderless" style={{ marginTop: 24, textAlign: 'center' }}>
                    <CheckCircleOutlined style={{ fontSize: 64, color: '#52c41a', marginBottom: 24 }} />
                    <Title level={3}>Ready to Sync</Title>
                    <Text type="secondary">Transactions have been mapped and are ready for Tally.</Text>

                    <div style={{ marginTop: 40 }}>
                        <Space size="large">
                            <Button size="large" icon={<DownloadOutlined />}>Download XML</Button>
                            <Button size="large" type="primary" icon={<CloudUploadOutlined />}>Push to Tally</Button>
                        </Space>
                    </div>
                    <div style={{ marginTop: 24 }}>
                        <Button type="link" onClick={() => { setCurrent(0); setPdfResult(null); setPdfWarnings([]); }}>Start New Import</Button>
                    </div>
                </Card>
            ),
        },
    ];

    const items = steps.map((item) => ({ key: item.title, title: item.title }));

    return (
        <div>
            <div style={{ marginBottom: 24 }}>
                <Title level={3} style={{ margin: 0 }}>Banking Import</Title>
                <Text type="secondary">Convert banking statements to Tally XML</Text>
            </div>

            <Steps current={current} items={items} />

            <div style={{ minHeight: '400px' }}>
                {steps[current].content}
            </div>
        </div>
    );
}
