#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
漫画整理工具主程序
"""
import argparse
import sys
from core.config import Config
from core.logger import logger
from services.transfer_service import TransferService
from services.organize_service import OrganizeService
from services.komga_service import KomgaService


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='manga',
        description='漫画整理和Komga管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # Tachiyomi转移
  %(prog)s transfer --debug                # 调试模式转移
  %(prog)s transfer                        # 正式转移
  
  # 漫画整理
  %(prog)s organize --debug                # 调试模式整理
  %(prog)s organize                        # 正式整理
  
  # Komga整理
  %(prog)s komga --debug                   # 调试模式整理Komga
  %(prog)s komga                           # 正式整理Komga
  
  # 组合操作
  %(prog)s transfer organize --debug       # 先转移后整理（调试模式）
  %(prog)s transfer organize --force       # 先转移后整理（强制执行）

更多信息请查看 README.md
        """
    )
    
    # 全局选项
    parser.add_argument(
        '-c', '--config',
        metavar='PATH',
        default='',
        help='指定配置文件路径（默认: manga.yaml）'
    )
    
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='调试模式，不实际执行操作（仅显示将要执行的操作）'
    )
    
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='强制执行模式，覆盖配置文件中的调试模式设置'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细输出模式'
    )
    
    # 操作命令（可多选）
    parser.add_argument(
        'transfer',
        nargs='?',
        action='store',
        const='transfer',
        help='从Tachiyomi转移漫画到Komga目录'
    )
    
    parser.add_argument(
        'organize',
        nargs='?',
        action='store',
        const='organize',
        help='整理漫画文件夹（优化命名和结构）'
    )
    
    parser.add_argument(
        'komga',
        nargs='?',
        action='store',
        const='komga',
        help='整理Komga库（更新元数据、按星级移动）'
    )
    
    return parser


def main():
    """主函数"""
    # 解析命令行参数
    parser = create_parser()
    
    # 特殊处理：支持多个位置参数作为命令
    args, unknown = parser.parse_known_args()
    
    # 收集要执行的操作
    actions = []
    if args.transfer:
        actions.append('transfer')
    if args.organize:
        actions.append('organize')
    if args.komga:
        actions.append('komga')
    
    # 处理未知参数，可能是操作命令
    for arg in unknown:
        if arg in ['transfer', 'organize', 'komga']:
            if arg not in actions:
                actions.append(arg)
    
    # 如果没有指定任何操作，显示帮助
    if not actions:
        parser.print_help()
        print("\n错误: 请至少指定一个操作命令 (transfer/organize/komga)")
        sys.exit(1)
    
    try:
        # 加载配置
        config = Config(args.config)
        
        # 设置执行模式
        if args.debug:
            config.dry_run = True
            logger.info("=" * 50)
            logger.info("=== 调试模式（Debug）- 不会实际修改文件 ===")
            logger.info("=" * 50)
        elif args.force:
            config.dry_run = False
            logger.info("=" * 50)
            logger.info("=== 强制执行模式（Force）- 将实际修改文件 ===")
            logger.info("=" * 50)
        else:
            mode = "调试模式" if config.dry_run else "正常执行模式"
            logger.info("=" * 50)
            logger.info(f"=== {mode} (由配置文件决定) ===")
            logger.info("=" * 50)
        
        # 显示详细模式
        if args.verbose:
            logger.logger.setLevel('DEBUG')
            logger.info("详细输出模式已启用")
        
        # 显示要执行的操作
        logger.info(f"将执行以下操作: {' -> '.join(actions)}\n")
        
        # 按顺序执行操作
        for action in actions:
            if action == 'transfer':
                logger.info(">>> 开始执行：Tachiyomi转移")
                logger.info("-" * 50)
                service = TransferService(config)
                service.transfer_manga()
                logger.info("-" * 50)
                logger.info(">>> Tachiyomi转移完成\n")
            
            elif action == 'organize':
                logger.info(">>> 开始执行：漫画整理")
                logger.info("-" * 50)
                service = OrganizeService(config)
                service.organize_manga()
                logger.info("-" * 50)
                logger.info(">>> 漫画整理完成\n")
            
            elif action == 'komga':
                logger.info(">>> 开始执行：Komga整理")
                logger.info("-" * 50)
                service = KomgaService(config)
                service.organize_komga_manga()
                logger.info("-" * 50)
                logger.info(">>> Komga整理完成\n")
        
        logger.info("=" * 50)
        logger.info("✓ 所有任务执行完成！")
        logger.info("=" * 50)
        
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("\n用户中断执行")
        sys.exit(130)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

