# config/agents.py
"""
エージェントの種類、クラス、表示名、パラメータなどの情報を一元管理するモジュール。
"""

# 利用可能なエージェントクラスをインポート
# --- 変更: 各モジュールから直接インポート ---
# from agents import FirstAgent, RandomAgent, GainAgent, MonteCarloTreeSearchAgent # 削除
# from agents.api_agent import ApiAgent # 削除

from agents.base_agent import Agent # 必要に応じて (現在は使われていないが念のため)
from agents.first_agent import FirstAgent
from agents.random_agent import RandomAgent
from agents.gain_agent import GainAgent
from agents.mcts_agent import MonteCarloTreeSearchAgent
from agents.api_agent import ApiAgent
# -----------------------------------------

# エージェント定義リスト
# 各要素は辞書形式:
#   'id': エージェントを一意に識別する整数ID (0は人間プレイヤー用に予約)
#   'class': 対応するエージェントクラス (人間プレイヤーの場合は None)
#   'display_name': GUIなどで表示される名前
#   'params': エージェントクラスの初期化時に渡すパラメータ (オプション)
AGENT_DEFINITIONS = [
    {
        'id': 0,
        'class': None,
        'display_name': '人間',
        'params': {}
    },
    {
        'id': 1,
        'class': FirstAgent,
        'display_name': 'First',
        'params': {}
    },
    {
        'id': 2,
        'class': RandomAgent,
        'display_name': 'Random',
        'params': {}
    },
    {
        'id': 3,
        'class': GainAgent,
        'display_name': 'Gain',
        'params': {}
    },
    {
        'id': 4,
        'class': MonteCarloTreeSearchAgent,
        'display_name': 'MCTS',
        'params': {
            'iterations': 50000,
            'time_limit_ms': 4000,
            'exploration_weight': 1.41
        }
        # 必要に応じて他のMCTSパラメータも追加可能
    },
    {
        'id': 5, # 新しいID (既存と重複しないように)
        'class': ApiAgent,
        'display_name': 'API (Random)',
        'params': {
            'api_url': 'http://127.0.0.1:5001/play', # デフォルトのAPIサーバーURL
            # timeout は ApiAgent のデフォルト値を使うか、必要ならここで指定
            # 'timeout': 10
        }
    },
    # --- 新しいエージェントを追加する場合は、ここに辞書を追加 ---
    # 例:
    # {
    #     'id': 6, # ID修正
    #     'class': YourNewAgent, # 適切にインポートしてください
    #     'display_name': 'NewAgent',
    #     'params': {'some_param': 'value'}
    # },
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
    print(f"警告: 指定されたエージェントID {agent_id} が見つかりません。") # デバッグ用
    return None # IDが見つからない場合

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
    print(f"警告: 指定されたエージェントID {agent_id} の定義が見つかりません。") # デバッグ用
    return None # IDが見つからない場合
