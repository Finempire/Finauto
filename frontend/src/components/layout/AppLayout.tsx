"use client";

import React, { useState } from 'react';
import { Layout, Menu, Typography, Avatar, Dropdown, Space } from 'antd';
import {
    HomeOutlined,
    BankOutlined,
    ShoppingCartOutlined,
    ShopOutlined,
    BookOutlined,
    SettingOutlined,
    UserOutlined,
    ApiOutlined
} from '@ant-design/icons';
import { useRouter, usePathname } from 'next/navigation';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

export default function AppLayout({ children }: { children: React.ReactNode }) {
    const [collapsed, setCollapsed] = useState(false);
    const router = useRouter();
    const pathname = usePathname();

    const menuItems = [
        { key: '/', icon: <HomeOutlined />, label: 'Home' },
        { key: '/banking', icon: <BankOutlined />, label: 'Banking Import' },
        { key: '/sales', icon: <ShopOutlined />, label: 'Sales' },
        { key: '/purchase', icon: <ShoppingCartOutlined />, label: 'Purchase' },
        { key: '/journal', icon: <BookOutlined />, label: 'Journal' },
        { key: '/ledger-mapping', icon: <ApiOutlined />, label: 'Ledger Mapping' },
        { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
    ];

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Sider
                collapsible
                collapsed={collapsed}
                onCollapse={(value) => setCollapsed(value)}
                theme="light"
                style={{ borderRight: '1px solid #f0f0f0' }}
            >
                <div style={{ padding: '16px', textAlign: 'center' }}>
                    {collapsed ? (
                        <Title level={4} style={{ margin: 0, color: '#1677ff' }}>T</Title>
                    ) : (
                        <Title level={4} style={{ margin: 0, color: '#1677ff' }}>Tally Auto</Title>
                    )}
                </div>
                <Menu
                    theme="light"
                    mode="inline"
                    selectedKeys={[pathname]}
                    items={menuItems}
                    onClick={(e) => router.push(e.key)}
                />
            </Sider>

            <Layout>
                <Header style={{
                    padding: '0 24px',
                    background: '#fff',
                    display: 'flex',
                    justifyContent: 'flex-end',
                    alignItems: 'center',
                    borderBottom: '1px solid #f0f0f0'
                }}>
                    <Dropdown menu={{ items: [{ key: '1', label: 'Settings' }, { key: '2', label: 'Logout' }] }}>
                        <Space style={{ cursor: 'pointer' }}>
                            <Avatar icon={<UserOutlined />} />
                            <Text>User</Text>
                        </Space>
                    </Dropdown>
                </Header>

                <Content style={{ margin: '24px 16px', padding: 24, minHeight: 280, background: '#fff', borderRadius: 8 }}>
                    {children}
                </Content>
            </Layout>
        </Layout>
    );
}
