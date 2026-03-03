"use client";

import React, { useState } from 'react';
import { Table, Input, Select, Button, Tag, Space, Typography, Progress, Card, Row, Col, Statistic } from 'antd';
import { SearchOutlined, CheckCircleOutlined, SyncOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

interface MappingRule {
    key: string;
    keyword: string;
    mappedLedger: string;
    status: 'Complete' | 'Partially Mapped' | 'Unmapped';
    source: 'User Rule' | 'Tally Sync' | 'AI Learned';
}

export default function LedgerMappingPage() {
    const [data, setData] = useState<MappingRule[]>([
        { key: '1', keyword: 'Amazon', mappedLedger: 'Office Supplies', status: 'Complete', source: 'User Rule' },
        { key: '2', keyword: 'Zomato', mappedLedger: 'Staff Welfare', status: 'Complete', source: 'AI Learned' },
        { key: '3', keyword: 'HDFC Bank', mappedLedger: 'HDFC CC A/c', status: 'Complete', source: 'Tally Sync' },
        { key: '4', keyword: 'Uber', mappedLedger: 'Conveyance', status: 'Partially Mapped', source: 'AI Learned' },
        { key: '5', keyword: 'Unknown Vendor', mappedLedger: '', status: 'Unmapped', source: 'User Rule' },
    ]);

    const tallyLedgers = ['Office Supplies', 'Staff Welfare', 'HDFC CC A/c', 'Conveyance', 'Suspense A/c', 'Rent A/c'];

    const columns = [
        {
            title: 'Bank Narration / Keyword',
            dataIndex: 'keyword',
            key: 'keyword',
            filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: any) => (
                <div style={{ padding: 8 }}>
                    <Input
                        placeholder="Search keyword"
                        value={selectedKeys[0]}
                        onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
                        onPressEnter={() => confirm()}
                        style={{ marginBottom: 8, display: 'block' }}
                    />
                    <Space>
                        <Button type="primary" onClick={() => confirm()} icon={<SearchOutlined />} size="small" style={{ width: 90 }}>Search</Button>
                        <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>Reset</Button>
                    </Space>
                </div>
            ),
            filterIcon: (filtered: boolean) => <SearchOutlined style={{ color: filtered ? '#1677ff' : undefined }} />,
            onFilter: (value: any, record: any) => record.keyword.toLowerCase().includes(value.toLowerCase()),
        },
        {
            title: 'Mapped Tally Ledger',
            dataIndex: 'mappedLedger',
            key: 'mappedLedger',
            render: (text: string, record: MappingRule) => (
                <Select
                    showSearch
                    style={{ width: 250 }}
                    placeholder="Select Ledger"
                    optionFilterProp="children"
                    defaultValue={text || undefined}
                    onChange={(val) => {
                        const newData = [...data];
                        const index = newData.findIndex(item => record.key === item.key);
                        if (index > -1) {
                            newData[index].mappedLedger = val;
                            newData[index].status = 'Complete';
                            setData(newData);
                        }
                    }}
                    options={tallyLedgers.map(l => ({ value: l, label: l }))}
                />
            )
        },
        {
            title: 'Source',
            dataIndex: 'source',
            key: 'source',
            render: (source: string) => {
                let color = source === 'Tally Sync' ? 'blue' : source === 'AI Learned' ? 'purple' : 'default';
                return <Tag color={color}>{source}</Tag>;
            }
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            filters: [
                { text: 'Complete', value: 'Complete' },
                { text: 'Partially Mapped', value: 'Partially Mapped' },
                { text: 'Unmapped', value: 'Unmapped' },
            ],
            onFilter: (value: any, record: any) => record.status === value,
            render: (status: string) => {
                let color = status === 'Complete' ? 'success' : status === 'Unmapped' ? 'error' : 'warning';
                return <Tag color={color}>{status}</Tag>;
            }
        },
        {
            title: 'Action',
            key: 'action',
            render: () => <Button type="link" danger>Delete</Button>
        }
    ];

    const mappedCount = data.filter(d => d.status === 'Complete').length;
    const percent = Math.round((mappedCount / data.length) * 100);

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                    <Title level={3} style={{ margin: 0 }}>Ledger Mapping Rules</Title>
                    <Text type="secondary">Manage how bank narrations map to Tally ledgers</Text>
                </div>
                <Space>
                    <Button icon={<SyncOutlined />}>Sync from Tally</Button>
                    <Button type="primary" icon={<CheckCircleOutlined />}>Save Rules</Button>
                </Space>
            </div>

            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col span={24}>
                    <Card variant="borderless" bodyStyle={{ padding: '16px 24px' }}>
                        <Row align="middle" justify="space-between">
                            <Col span={18}>
                                <Text strong>Mapping Completion Progress</Text>
                                <Progress percent={percent} status={percent === 100 ? "success" : "active"} strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }} />
                            </Col>
                            <Col span={6} style={{ textAlign: 'right' }}>
                                <Statistic title="Unmapped Rules" value={data.length - mappedCount} valueStyle={{ color: '#cf1322', fontSize: 24 }} />
                            </Col>
                        </Row>
                    </Card>
                </Col>
            </Row>

            <Card variant="borderless">
                <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
                    <Button type="dashed">+ Add Custom Rule</Button>
                </div>
                <Table
                    columns={columns}
                    dataSource={data}
                    pagination={{ pageSize: 10 }}
                />
            </Card>
        </div>
    );
}
