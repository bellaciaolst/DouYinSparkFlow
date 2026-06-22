def do_user_task(browser, username, cookies, targets):
    context = browser.new_context()  # 每个任务使用独立的上下文
    
    # 💡 强力降噪：针对 GitHub Actions 云端运行，单独把元素查找超时缩短到 15 秒
    # 这样就算卡住了，也会在 15 秒内报错弹出来，而不是死等 2 分钟
    context.set_default_navigation_timeout(config["browserTimeout"])  # 导航超时仍可保持较长
    context.set_default_timeout(15000)  # 查找元素超过 15 秒直接报错，防止死等挂起

    page = context.new_page()
    
    if matchMode == "short_id":  # 使用抖音号进行匹配
        page.on("response", handle_response)
    
    # 1. 必须先注入 Cookie 
    context.add_cookies(cookies)

    # 2. 🎯 核心抗卡死修改：放弃打开创作者中心首页，直接一步到位去聊天消息页面！
    # 首页含有大量反爬、滑块和重定向逻辑，在 Actions 的 headless 环境中极易永久卡死
    logger.info(f"账号 {username} 正在直接跨越到消息页面...")
    try:
        page.goto(
            "https://creator.douyin.com/creator-micro/data/following/chat",
            wait_until="commit", # 💡 只要服务器响应了就立刻继续，不等垃圾静态资源加载完毕，防卡死
            timeout=45000
        )
    except Exception as e:
        logger.warning(f"账号 {username} 页面加载未完全结束（可能在等冗余资源），尝试继续：{e}")

    # 给页面 DOM 渲染留 5 秒死权重缓冲
    time.sleep(5)

    logger.debug(f"账号 {username} 开始发送消息流")
    
    try:
        # 滚动并选择用户
        for target_username in scroll_and_select_user(page, username, targets):
            logger.debug(f"账号 {username} 已选中好友 {target_username} 发送消息")
            
            # 等待聊天输入框元素加载完成
            chat_input_selector = "xpath=//div[contains(@class, 'chat-input-')]"
            page.wait_for_selector(chat_input_selector, timeout=10000)
            chat_input = page.locator(chat_input_selector)

            # 输入内容
            message = build_message()
            message_lines = message.split("\\n")
            for line in message_lines:
                chat_input.type(line)  # 输入每一行
                if line != message_lines[-1]:
                    chat_input.press("Shift+Enter")

            logger.debug(
                f"账号 {username} 准备发送消息给好友 {target_username}：\n\t{message}"
            )
            
            # 模拟按下回车键发送消息
            chat_input.press("Enter")
            logger.debug(f"账号 {username} 给好友 {target_username} 发送消息完成")
            time.sleep(2)  # 发送完等待一会儿
            
    except Exception as e:
        # 💡 如果卡死在某一步导致失败，立刻保存一张当前网页的截图到 logs 目录！
        # 这样你在 GitHub 的 artifacts 下载日志包，就能一眼看到当时浏览器里到底是卡在什么画面了（比如是不是弹滑块了）
        import os
        os.makedirs("logs", exist_ok=True)
        screenshot_path = f"logs/{username}_error.png"
        try:
            page.screenshot(path=screenshot_path)
            logger.error(f"❌ 运行中遭遇异常，已自动保存错误截图至: {screenshot_path}。错误详情: {e}")
        except:
            logger.error(f"❌ 运行中遭遇异常，且无法截屏。错误详情: {e}")
        raise e # 重新抛出，让这一轮任务正常终止，而不是挂起

    finally:
        context.close()  # 任务完成后关闭上下文
