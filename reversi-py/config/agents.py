# config/agents.py
"""
エージェントの種類、クラス、表示名、パラメータなどの情報を一元管理するモジュール。
"""

# 利用可能なエージェントクラスをインポート
# このファイルの場所に応じてインポートパスを調整する必要がある場合があります。
# 例: プロジェクトルートに agents.py がある場合
from agents import FirstAgent, RandomAgent, GainAgent, MonteCarloTreeSearchAgent
# 例: agents.py が config と同じ階層にある場合
# from ..agents import FirstAgent, RandomAgent, GainAgent, MonteCarloTreeSearchAgent

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
    # --- 新しいエージェントを追加する場合は、ここに辞書を追加 ---
    # 例:
    # {
    #     'id': 5,
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

def get_agent_params(agent_id):
    """
    指定されたIDに対応するエージェントの初期化パラメータを返す。
    Args:
        agent_id (int): エージェントID
    Returns:
        dict: 初期化パラメータの辞書。IDが見つからない場合は空の辞書を返す。
    """
    for agent in AGENT_DEFINITIONS:
        if agent['id'] == agent_id:
            # params キーが存在しない場合に備えて get を使う
            return agent.get('params', {})
    print(f"警告: 指定されたエージェントID {agent_id} のパラメータが見つかりません。") # デバッグ用
    return {} # IDが見つからない場合

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

