from config.agents import AGENT_DEFINITIONS

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
