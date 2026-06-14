# config/agents_config.py
"""
エージェントの種類、クラス、表示名、パラメータなどの情報を一元管理するモジュール。
"""

import logging

from agents.api_agent import ApiAgent

logger = logging.getLogger(__name__)

# エージェント定義リスト (人間 + API 系のエージェント)
# 各要素は辞書形式:
#   'id': エージェントを一意に識別する整数ID (0は人間プレイヤー用に予約)
#   'class': 対応するエージェントクラス (人間プレイヤーの場合は None)
#   'display_name': GUIなどで表示される名前
#   'params': エージェントクラスの初期化時に渡すパラメータ
AGENT_DEFINITIONS = [
    {
        'id': 0,
        'class': None,
        'display_name': '人間',
        'params': {}
    },
    {
        'id': 1,
        'class': ApiAgent,
        'display_name': 'API (First)',
        'params': {
            'api_url': 'http://127.0.0.1:5001/play',
            'agent_type': 'first',
        }
    },
    {
        'id': 2,
        'class': ApiAgent,
        'display_name': 'API (Random)',
        'params': {
            'api_url': 'http://127.0.0.1:5001/play',
            'agent_type': 'random',
        }
    },
    {
        'id': 3,
        'class': ApiAgent,
        'display_name': 'API (Gain)',
        'params': {
            'api_url': 'http://127.0.0.1:5001/play',
            'agent_type': 'gain',
        }
    },
    {
        'id': 4,
        'class': ApiAgent,
        'display_name': 'API (MCTS)',
        'params': {
            'api_url': 'http://127.0.0.1:5001/play',
            'agent_type': 'mcts',
        }
    },
    {
        'id': 5,
        'class': ApiAgent,
        'display_name': 'API (Negamax)',
        'params': {
            'api_url': 'http://127.0.0.1:5001/play',
            'agent_type': 'negamax',
        }
    },
    {
        'id': 6,
        'class': ApiAgent,
        'display_name': 'API (Transposition)',
        'params': {
            'api_url': 'http://127.0.0.1:5001/play',
            'agent_type': 'transposition',
        }
    },
    {
        'id': 7,
        'class': ApiAgent,
        'display_name': 'API (Pattern)',
        'params': {
            'api_url': 'http://127.0.0.1:5001/play',
            'agent_type': 'pattern',
        }
    },
]

# --- ヘルパー関数 ---

def get_agent_options():
    """
    GUIのラジオボタンなどで使用するためのエージェント選択肢リストを返す。
    Returns:
        list[tuple[int, str]]: (id, display_name) のタプルのリスト
    """
    return [(agent['id'], agent['display_name']) for agent in AGENT_DEFINITIONS]

def get_agent_class(agent_id):
    """
    指定されたIDに対応するエージェントクラスを返す。
    Args:
        agent_id (int): エージェントID
    Returns:
        type | None: 対応するエージェントクラス、または人間プレイヤーの場合は None。
                     IDが見つからない場合も None を返す。
    """
    for agent in AGENT_DEFINITIONS:
        if agent['id'] == agent_id:
            return agent['class']
    logger.warning(f"Specified agent ID {agent_id} not found.")
    return None

def get_agent_definition(agent_id):
    """
    指定されたIDに対応するエージェントの完全な定義辞書を返す。
    Args:
        agent_id (int): エージェントID
    Returns:
        dict | None: 対応するエージェントの定義辞書。IDが見つからない場合は None を返す。
    """
    for agent in AGENT_DEFINITIONS:
        if agent['id'] == agent_id:
            return agent
    logger.warning(f"Agent definition for ID {agent_id} not found.")
    return None
