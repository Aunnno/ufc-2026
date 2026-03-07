#!/usr/bin/env python3
# test_user_api.py
# 用户API测试脚本

import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api/user"

def test_create_user():
    """测试创建用户"""
    print("测试创建用户...")
    
    # 生成随机用户名
    test_name = f"测试用户_{uuid.uuid4().hex[:8]}"
    
    response = requests.get(f"{BASE_URL}/create", params={"name": test_name})
    
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            user_id = data["data"]["user_id"]
            print(f"✓ 创建用户成功: ID={user_id}, 姓名={test_name}")
            return user_id
        else:
            print("✗ 创建用户失败")
    else:
        print("✗ HTTP请求失败")
    
    return None

def test_get_user(user_id):
    """测试获取用户信息"""
    print(f"\n测试获取用户信息 (ID: {user_id})...")
    
    response = requests.get(f"{BASE_URL}/get", params={"id": user_id})
    
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            user_data = data["data"]
            print(f"✓ 获取用户成功: {user_data}")
            return user_data
        else:
            print("✗ 获取用户失败")
    else:
        print("✗ HTTP请求失败")
    
    return None

def test_update_medicine(user_id):
    """测试更新药物列表"""
    print(f"\n测试更新药物列表 (ID: {user_id})...")
    
    medicine_list = "阿司匹林,维生素C,降压药"
    
    response = requests.post(
        f"{BASE_URL}/update_medicine",
        params={"user_id": user_id, "medicine": medicine_list}
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"✓ 更新药物列表成功: {medicine_list}")
            return True
        else:
            print("✗ 更新药物列表失败")
    else:
        print("✗ HTTP请求失败")
    
    return False

def test_upload_face_image():
    """测试上传人脸图片（需要实际图片文件）"""
    print("\n测试上传人脸图片...")
    print("注意：此测试需要实际的图片文件，请手动测试")
    return True

def test_recognize_face():
    """测试人脸识别（需要已上传的图片和注册的人脸）"""
    print("\n测试人脸识别...")
    print("注意：此测试需要已上传的人脸图片和已注册的人脸数据，请手动测试")
    return True

def main():
    """主测试函数"""
    print("=== 用户API测试开始 ===\n")
    
    # 测试创建用户
    user_id = test_create_user()
    
    if user_id:
        # 测试获取用户信息
        test_get_user(user_id)
        
        # 测试更新药物列表
        test_update_medicine(user_id)
        
        # 再次获取用户信息，验证药物更新
        test_get_user(user_id)
    
    # 提示其他测试需要手动进行
    test_upload_face_image()
    test_recognize_face()
    
    print("\n=== 用户API测试完成 ===")
    print("\nAPI端点总结:")
    print(f"1. 创建用户: GET {BASE_URL}/create?name=<用户名>")
    print(f"2. 获取用户: GET {BASE_URL}/get?id=<用户ID>")
    print(f"3. 上传人脸: POST {BASE_URL}/upload_face_img (multipart/form-data)")
    print(f"4. 识别人脸: GET {BASE_URL}/recognize_face")
    print(f"5. 注册人脸: POST {BASE_URL}/register_face?user_id=<用户ID>")
    print(f"6. 更新药物: POST {BASE_URL}/update_medicine?user_id=<用户ID>&medicine=<药物列表>")

if __name__ == "__main__":
    main()