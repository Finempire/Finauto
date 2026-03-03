"use client";

import React from 'react';
import { Row, Col, Card, Typography, Button, Space } from 'antd';
import {
  BankOutlined,
  ShopOutlined,
  BookOutlined,
  ShoppingCartOutlined,
  ApiOutlined,
  RocketOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';

const { Title, Text } = Typography;

const tools = [
  {
    key: '/banking',
    icon: <BankOutlined style={{ fontSize: 36, color: '#1677ff' }} />,
    title: 'Banking Import',
    description: 'Upload bank statement CSV/XLSX, map ledgers, generate Tally XML or push directly.',
  },
  {
    key: '/sales',
    icon: <ShopOutlined style={{ fontSize: 36, color: '#52c41a' }} />,
    title: 'Sales Vouchers',
    description: 'Convert sales invoices with GST breakup into Tally-ready XML.',
  },
  {
    key: '/purchase',
    icon: <ShoppingCartOutlined style={{ fontSize: 36, color: '#faad14' }} />,
    title: 'Purchase / Credit Note',
    description: 'Import purchase invoices or credit notes and generate XML.',
  },
  {
    key: '/journal',
    icon: <BookOutlined style={{ fontSize: 36, color: '#722ed1' }} />,
    title: 'Journal Entries',
    description: 'Map fixed & dynamic ledger columns and convert journals to XML.',
  },
  {
    key: '/ledger-mapping',
    icon: <ApiOutlined style={{ fontSize: 36, color: '#13c2c2' }} />,
    title: 'Ledger Mapping Rules',
    description: 'Configure narration-to-ledger mapping rules for auto-matching.',
  },
];

export default function HomePage() {
  const router = useRouter();

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <RocketOutlined style={{ fontSize: 48, color: '#1677ff', marginBottom: 8 }} />
        <Title level={2} style={{ margin: 0 }}>Tally Automation</Title>
        <Text type="secondary" style={{ fontSize: 16 }}>
          Upload → Map Ledgers → Push to Tally or Download XML
        </Text>
      </div>

      <Row gutter={[24, 24]} justify="center">
        {tools.map((tool) => (
          <Col xs={24} sm={12} lg={8} key={tool.key}>
            <Card
              hoverable
              variant="borderless"
              style={{ textAlign: 'center', height: '100%', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
              onClick={() => router.push(tool.key)}
            >
              <div style={{ marginBottom: 16 }}>{tool.icon}</div>
              <Title level={4} style={{ margin: 0 }}>{tool.title}</Title>
              <Text type="secondary" style={{ display: 'block', marginTop: 8, fontSize: 13 }}>
                {tool.description}
              </Text>
              <Button type="primary" style={{ marginTop: 20 }}>Open →</Button>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}
