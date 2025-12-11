from flask import Blueprint, render_template

bp = Blueprint('ai', __name__, url_prefix='/ai')

@bp.route('/ai')
def ai():
    """
    생성형 AI 메인 화면
    """
    return render_template('main/ai.html')