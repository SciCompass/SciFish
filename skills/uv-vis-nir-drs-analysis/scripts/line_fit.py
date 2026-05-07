import numpy as np
from sklearn.linear_model import LinearRegression


def find_linear_correlation_region(x_data, y_data, R_tol=0.999, min_segment_points=2):
    TAUC_X_orig = np.array(x_data).reshape(-1, 1)
    TAUC_Y_orig = np.array(y_data).reshape(-1, 1)  # 假设分析直接带隙

    X0 = [TAUC_X_orig]  # 初始化 X 值
    Y0 = [TAUC_Y_orig]  # 初始化 Y 值

    X_tol = []  # 存储满足 R_tol 的 X 数据段
    Y_tol = []  # 存储满足 R_tol 的 Y 数据段

    processed_segments_count = 0  # 记录已处理并放入X_tol的点数

    # --- 递归分段 ---
    # 为了避免无限递归或过小的分段，我们需要更精细地控制循环
    # 当X0为空时，表示所有段要么满足条件，要么小到不能再分
    while X0:  # 当还有段需要处理时
        X_next_round = []  # 存储下一轮需要处理的X段
        Y_next_round = []  # 存储下一轮需要处理的Y段

        processed_this_round = False
        for segX, segY in zip(X0, Y0):
            if len(segX) < min_segment_points:  # 如果段太短，不再分割，也不一定满足R_tol
                # 可以选择将其加入一个“剩余段”列表，或根据策略决定是否尝试拟合
                # 为简单起见，如果太短，我们这里先不强制加入X_tol
                # 另一种策略是，如果len(segX) >= 2，即使小于min_segment_points，也尝试拟合一次
                if len(segX) >= 2:  # 至少2个点才能拟合
                    model_short = LinearRegression().fit(segX, segY)
                    if model_short.score(segX, segY) >= R_tol:
                        X_tol.append(segX)
                        Y_tol.append(segY)
                        processed_segments_count += len(segX)
                        processed_this_round = True
                    # else: # 太短且不满足，则丢弃或放入X_next_round（如果希望强制分割）
                    # 这里我们选择不进一步分割非常短且不满足条件的段
                continue  # 跳过太短的段的进一步分割

            model_full_seg = LinearRegression().fit(segX, segY)
            if model_full_seg.score(segX, segY) >= R_tol:
                X_tol.append(segX)
                Y_tol.append(segY)
                processed_segments_count += len(segX)
                processed_this_round = True
                continue  # 整个段满足条件，不再分割

            # 如果整个段不满足，则尝试分割
            mid = len(segX) // 2
            if mid < 1 or len(segX) - mid < 1:  # 避免产生空段
                continue

            # 左段 (确保至少有min_segment_points，或者至少2个点)
            X_L, Y_L = segX[:mid + 1], segY[:mid + 1]
            if len(X_L) >= 2:  # 至少2个点才能构成段
                # 这里不再立即检查R_tol，而是将其放入下一轮处理
                # 这样可以避免对刚刚分割出来的小段立即做R_tol判断，给它们机会被进一步细分
                X_next_round.append(X_L)
                Y_next_round.append(Y_L)
                processed_this_round = True

            # 右段
            X_R, Y_R = segX[mid:], segY[mid:]
            if len(X_R) >= 2:
                X_next_round.append(X_R)
                Y_next_round.append(Y_R)
                processed_this_round = True

        X0 = X_next_round
        Y0 = Y_next_round

        # 检查循环终止条件：如果X0为空，或者没有段被处理/分割，则退出
        if not X0 or not processed_this_round:
            # 如果X0中还有未处理的段，且它们都太短无法分割，将它们加入X_tol（如果它们满足R_tol）
            for final_segX, final_segY in zip(X0, Y0):
                if len(final_segX) >= 2:
                    model_final = LinearRegression().fit(final_segX, final_segY)
                    if model_final.score(final_segX, final_segY) >= R_tol:
                        X_tol.append(final_segX)
                        Y_tol.append(final_segY)
            break
    # --- 递归分段结束 ---

    if not X_tol:
        return [], [], [], [], []

    # --- 排序找到的线性段 ---
    medians = [np.median(l) for l in X_tol]
    sort_mask = np.argsort(medians)
    # 使用列表推导式来正确排序，因为np.array(X_tol, dtype=object)在numpy版本高时可能行为不一致
    X_tol_sort = [X_tol[i] for i in sort_mask]
    Y_tol_sort = [Y_tol[i] for i in sort_mask]

    # --- 后处理：合并相邻的线性段 ---
    if not X_tol_sort:  # 如果没有找到任何段
        return [], [], [], [], []

    merged_X = []
    merged_Y = []
    slopes_merged = []
    intercepts_merged = []
    r_squared_merged = []

    if X_tol_sort:  # 确保列表不为空
        current_X_seg = X_tol_sort[0].copy()  # 使用 .copy()
        current_Y_seg = Y_tol_sort[0].copy()

        for i in range(1, len(X_tol_sort)):
            next_X_seg = X_tol_sort[i]
            next_Y_seg = Y_tol_sort[i]

            # 尝试合并 current_seg 和 next_seg
            prospective_X = np.concatenate((current_X_seg, next_X_seg))
            prospective_Y = np.concatenate((current_Y_seg, next_Y_seg))

            # 重新排序合并后的X，并对应调整Y (非常重要，因为段可能不完全连续)
            # 并且去除重复点 (如果hv值完全相同)
            unique_prospective_X, unique_indices = np.unique(prospective_X, return_index=True)
            unique_prospective_Y = prospective_Y[unique_indices]

            # 确保排序是hv升序
            sort_order = np.argsort(unique_prospective_X.ravel())  # .ravel() 确保是一维
            sorted_prospective_X = unique_prospective_X[sort_order].reshape(-1, 1)
            sorted_prospective_Y = unique_prospective_Y[sort_order].reshape(-1, 1)

            if len(sorted_prospective_X) < 2:  # 合并后点太少
                # 将之前的 current_X_seg 保存下来
                model_prev = LinearRegression().fit(current_X_seg, current_Y_seg)
                merged_X.append(current_X_seg)
                merged_Y.append(current_Y_seg)
                slopes_merged.append(model_prev.coef_[0, 0])
                intercepts_merged.append(model_prev.intercept_[0])
                r_squared_merged.append(model_prev.score(current_X_seg, current_Y_seg))
                # 将 next_seg 作为新的 current_seg
                current_X_seg = next_X_seg.copy()
                current_Y_seg = next_Y_seg.copy()
                continue

            model_merged = LinearRegression().fit(sorted_prospective_X, sorted_prospective_Y)
            if model_merged.score(sorted_prospective_X, sorted_prospective_Y) >= R_tol:
                # 合并成功，更新 current_seg
                current_X_seg = sorted_prospective_X
                current_Y_seg = sorted_prospective_Y
            else:
                # 合并失败，将旧的 current_seg 保存
                model_prev = LinearRegression().fit(current_X_seg, current_Y_seg)
                merged_X.append(current_X_seg)
                merged_Y.append(current_Y_seg)
                slopes_merged.append(model_prev.coef_[0, 0])
                intercepts_merged.append(model_prev.intercept_[0])
                r_squared_merged.append(model_prev.score(current_X_seg, current_Y_seg))
                # 将 next_seg 作为新的 current_seg
                current_X_seg = next_X_seg.copy()
                current_Y_seg = next_Y_seg.copy()

        # 添加最后一个 current_seg
        if len(current_X_seg) >= 2:
            model_last = LinearRegression().fit(current_X_seg, current_Y_seg)
            merged_X.append(current_X_seg)
            merged_Y.append(current_Y_seg)
            slopes_merged.append(model_last.coef_[0, 0])
            intercepts_merged.append(model_last.intercept_[0])
            r_squared_merged.append(model_last.score(current_X_seg, current_Y_seg))
    # --- 合并结束 ---

    # 返回合并后的结果
    # 注意：这里我们返回了所有合并后的段及其参数
    # 在实际应用中，你可能需要进一步选择“最佳”段来计算Eg
    return merged_X, merged_Y, slopes_merged, intercepts_merged, r_squared_merged
